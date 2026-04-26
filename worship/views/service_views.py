import json
import html
import re
from datetime import datetime

import weasyprint
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.core_context_processor import context_user_data
from worship.forms import WorshipServiceForm, WorshipServiceImportForm, WorshipServiceSongForm
from worship.models import Song, WorshipService, WorshipServiceSong
from worship.utils import generate_service_with_llm, resolve_song_reference


def _is_worship_member(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff or user.type == "REGULAR"


def _normalize_single_line(text):
    text = (text or "").replace("\r", " ").replace("\n", " / ")
    text = re.sub(r"\s+/\s+", " / ", text)
    text = re.sub(r"\s+", " ", text).strip(" /")
    return text


def _compose_leaders_text(form):
    parts = []
    d = form.cleaned_data.get("leader_dirigente", "")
    r = form.cleaned_data.get("leader_regente", "")
    m = form.cleaned_data.get("leader_musician", "")
    if d:
        parts.append(f"Dirigente: {d.strip()}")
    if r:
        parts.append(f"Regente: {r.strip()}")
    if m:
        parts.append(f"Pianista: {m.strip()}")
    return " / ".join(parts) if parts else ""


def _clamp_font_scale(value):
    return max(75, min(130, int(value)))


class WorshipAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return _is_worship_member(self.request.user)


class WorshipServiceListView(WorshipAccessMixin, ListView):
    template_name = "worship/service_list.html"
    model = WorshipService
    context_object_name = "services"

    def get_queryset(self):
        queryset = WorshipService.objects.all()
        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(title__icontains=q)
        return queryset


class WorshipServiceCreateView(WorshipAccessMixin, CreateView):
    template_name = "worship/service_form.html"
    model = WorshipService
    form_class = WorshipServiceForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.leaders_text = _compose_leaders_text(form) or _normalize_single_line(form.cleaned_data.get("leaders_text"))
        response = super().form_valid(form)
        messages.success(self.request, "Culto criado com sucesso.")
        return response

    def get_success_url(self):
        return reverse("worship:service-detail", kwargs={"pk": self.object.pk})


class WorshipServiceUpdateView(WorshipAccessMixin, UpdateView):
    template_name = "worship/service_form.html"
    model = WorshipService
    form_class = WorshipServiceForm

    def get_success_url(self):
        messages.success(self.request, "Culto atualizado com sucesso.")
        return reverse("worship:service-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        form.instance.leaders_text = _compose_leaders_text(form) or _normalize_single_line(form.cleaned_data.get("leaders_text"))
        return super().form_valid(form)


class WorshipServiceDeleteView(WorshipAccessMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(WorshipService, pk=pk)
        service.delete()
        messages.success(request, "Culto excluído.")
        return redirect("worship:service-list")


class WorshipServiceDetailView(WorshipAccessMixin, DetailView):
    template_name = "worship/service_detail.html"
    model = WorshipService
    context_object_name = "service"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["song_form"] = WorshipServiceSongForm()
        context["program_font_scale"] = _clamp_font_scale(self.object.program_font_scale)
        context["pending_songs"] = self.object.sung_songs.filter(resolution_status=WorshipServiceSong.RESOLUTION_PENDING_REVIEW)
        context["song_choices"] = Song.objects.order_by("title")
        return context


class WorshipServiceDuplicateView(WorshipAccessMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(WorshipService, pk=pk)
        with transaction.atomic():
            new_service = WorshipService.objects.create(
                title=service.title,
                service_kind=service.service_kind,
                service_date=service.service_date,
                service_time=service.service_time,
                leaders_text=service.leaders_text,
                program_html=service.program_html,
                notes=service.notes,
                created_by=request.user,
            )
            for song in service.sung_songs.all():
                WorshipServiceSong.objects.create(
                    service=new_service,
                    song=song.song,
                    song_snapshot=song.song_snapshot,
                    source=song.source,
                    order_ref=song.order_ref,
                    resolution_status=song.resolution_status,
                    detected_hymnal_raw=song.detected_hymnal_raw,
                    detected_hymnal=song.detected_hymnal,
                    detected_number=song.detected_number,
                    match_confidence=song.match_confidence,
                    resolution_note=song.resolution_note,
                )
        messages.success(request, "Culto duplicado com sucesso.")
        return redirect("worship:service-edit", pk=new_service.pk)


class WorshipServiceSongCreateView(WorshipAccessMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(WorshipService, pk=pk)
        form = WorshipServiceSongForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.service = service
            entry.source = WorshipServiceSong.SOURCE_MANUAL
            if not entry.order_ref:
                last_order = service.sung_songs.exclude(order_ref__isnull=True).order_by("-order_ref").values_list("order_ref", flat=True).first() or 0
                entry.order_ref = last_order + 1
            if entry.song and not entry.song_snapshot:
                entry.song_snapshot = entry.song.title
            if entry.song:
                entry.resolution_status = WorshipServiceSong.RESOLUTION_LINKED
            else:
                resolution = resolve_song_reference(entry.song_snapshot)
                entry.song = resolution["song"]
                entry.resolution_status = resolution["resolution_status"]
                entry.detected_hymnal_raw = resolution["detected_hymnal_raw"]
                entry.detected_hymnal = resolution["detected_hymnal"]
                entry.detected_number = resolution["detected_number"]
                entry.match_confidence = resolution["match_confidence"]
                entry.resolution_note = resolution["resolution_note"]
                if entry.song and entry.resolution_status != WorshipServiceSong.RESOLUTION_UNLINKED:
                    entry.resolution_status = WorshipServiceSong.RESOLUTION_LINKED
            entry.save()
            messages.success(request, "Canção registrada.")
        else:
            messages.error(request, "Não foi possível registrar a canção.")
        return redirect("worship:service-detail", pk=pk)


class WorshipServiceSongDeleteView(WorshipAccessMixin, View):
    def post(self, request, pk, song_id):
        service = get_object_or_404(WorshipService, pk=pk)
        entry = get_object_or_404(WorshipServiceSong, pk=song_id, service=service)
        entry.delete()
        messages.success(request, "Registro de canção removido.")
        return redirect("worship:service-detail", pk=pk)


class WorshipServiceSongResolveView(WorshipAccessMixin, View):
    def post(self, request, pk, song_id):
        service = get_object_or_404(WorshipService, pk=pk)
        entry = get_object_or_404(WorshipServiceSong, pk=song_id, service=service)

        action = request.POST.get("action", "")
        note = (request.POST.get("resolution_note", "") or "").strip()

        if action == "link":
            target_song_id = request.POST.get("song")
            if not target_song_id:
                messages.error(request, "Selecione uma canção para vincular.")
                return redirect("worship:service-detail", pk=pk)
            song = get_object_or_404(Song, pk=target_song_id)
            entry.song = song
            entry.song_snapshot = entry.song_snapshot or song.title
            entry.resolution_status = WorshipServiceSong.RESOLUTION_LINKED
            entry.match_confidence = 1
            entry.resolution_note = note or "Vinculada manualmente."
        elif action == "unlink":
            entry.song = None
            entry.resolution_status = WorshipServiceSong.RESOLUTION_UNLINKED
            if entry.detected_hymnal and entry.detected_number and not note:
                entry.resolution_note = f"Mantida avulsa. Origem detectada: {entry.detected_hymnal.title} {entry.detected_number}"
            else:
                entry.resolution_note = note or "Mantida como avulsa."
        elif action == "retry":
            resolution = resolve_song_reference(entry.song_snapshot)
            entry.song = resolution["song"]
            entry.resolution_status = resolution["resolution_status"]
            entry.detected_hymnal_raw = resolution["detected_hymnal_raw"]
            entry.detected_hymnal = resolution["detected_hymnal"]
            entry.detected_number = resolution["detected_number"]
            entry.match_confidence = resolution["match_confidence"]
            entry.resolution_note = resolution["resolution_note"]
            if entry.song and entry.resolution_status != WorshipServiceSong.RESOLUTION_UNLINKED:
                entry.resolution_status = WorshipServiceSong.RESOLUTION_LINKED
        else:
            messages.error(request, "Ação inválida para resolver registro.")
            return redirect("worship:service-detail", pk=pk)

        entry.save()
        messages.success(request, "Registro de canção atualizado.")
        return redirect("worship:service-detail", pk=pk)


class WorshipServiceFontScaleView(WorshipAccessMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(WorshipService, pk=pk)
        action = request.POST.get("action", "")
        current = _clamp_font_scale(service.program_font_scale)

        if action == "increase":
            current += 5
        elif action == "decrease":
            current -= 5
        elif action == "reset":
            current = 100

        service.program_font_scale = _clamp_font_scale(current)
        service.save(update_fields=["program_font_scale"])
        return redirect("worship:service-detail", pk=pk)


def _extract_songs_from_program_html(program_html):
    if not program_html:
        return []

    plain = re.sub(r"<br\s*/?>", "\n", program_html, flags=re.IGNORECASE)
    plain = re.sub(r"</(p|li|div|h1|h2|h3|h4|h5|h6|ol|ul)>", "\n", plain, flags=re.IGNORECASE)
    plain = re.sub(r"<[^>]+>", "", plain)
    plain = html.unescape(plain)

    songs = []
    for idx, line in enumerate([ln.strip() for ln in plain.splitlines() if ln.strip()], start=1):
        lower = line.lower()
        if "hino" in lower or re.search(r"\b(CC|VM|HA|HL)\b", line, flags=re.IGNORECASE):
            snapshot = re.sub(r"^\d+\.\s*", "", line).strip()
            snapshot = snapshot.replace("Hino:", "").strip()
            if snapshot:
                songs.append({"order_ref": idx, "song_snapshot": snapshot})
    return songs


class WorshipServiceSongSyncFromProgramView(WorshipAccessMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(WorshipService, pk=pk)
        songs = _extract_songs_from_program_html(service.program_html)
        if not songs:
            messages.warning(request, "Nenhuma canção foi detectada na programação.")
            return redirect("worship:service-detail", pk=pk)

        with transaction.atomic():
            service.sung_songs.filter(source=WorshipServiceSong.SOURCE_IMPORTED).delete()
            count = 0
            for song in songs:
                snapshot = song["song_snapshot"]
                resolution = resolve_song_reference(snapshot)
                WorshipServiceSong.objects.create(
                    service=service,
                    song=resolution["song"],
                    song_snapshot=snapshot,
                    source=WorshipServiceSong.SOURCE_IMPORTED,
                    order_ref=song.get("order_ref"),
                    resolution_status=resolution["resolution_status"],
                    detected_hymnal_raw=resolution["detected_hymnal_raw"],
                    detected_hymnal=resolution["detected_hymnal"],
                    detected_number=resolution["detected_number"],
                    match_confidence=resolution["match_confidence"],
                    resolution_note=resolution["resolution_note"],
                )
                count += 1

        messages.success(request, f"{count} canções importadas da programação.")
        return redirect("worship:service-detail", pk=pk)


class WorshipServiceGenerateProgramView(WorshipAccessMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(WorshipService, pk=pk)
        raw_text = request.POST.get("raw_text", "").strip()
        model_hint = request.POST.get("model_hint", "").strip()
        if not raw_text:
            messages.error(request, "Cole o texto base para gerar com IA.")
            return redirect("worship:service-edit", pk=pk)

        payload = generate_service_with_llm(raw_text, model_hint=model_hint)
        service.title = payload.get("title") or service.title
        service.service_kind = payload.get("service_kind") or service.service_kind
        if payload.get("service_date"):
            raw = payload["service_date"]
            service.service_date = raw if not isinstance(raw, str) else datetime.strptime(raw, "%Y-%m-%d").date()
        service.leaders_text = _normalize_single_line(payload.get("leaders_text", ""))
        service.program_html = payload.get("program_html", "")
        service.save()

        if payload.get("songs"):
            service.sung_songs.filter(source=WorshipServiceSong.SOURCE_IMPORTED).delete()
            for song in payload["songs"]:
                snapshot = song.get("song_snapshot", "").strip()
                if not snapshot:
                    continue
                resolution = resolve_song_reference(snapshot)
                WorshipServiceSong.objects.create(
                    service=service,
                    song=resolution["song"],
                    song_snapshot=snapshot,
                    source=WorshipServiceSong.SOURCE_IMPORTED,
                    order_ref=song.get("order_ref"),
                    resolution_status=resolution["resolution_status"],
                    detected_hymnal_raw=resolution["detected_hymnal_raw"],
                    detected_hymnal=resolution["detected_hymnal"],
                    detected_number=resolution["detected_number"],
                    match_confidence=resolution["match_confidence"],
                    resolution_note=resolution["resolution_note"],
                )

        messages.success(request, "Programação gerada com IA e aplicada no culto.")
        return redirect("worship:service-edit", pk=pk)


class WorshipServiceImportView(WorshipAccessMixin, View):
    template_name = "worship/service_import.html"

    def get(self, request):
        return render(request, self.template_name, {"form": WorshipServiceImportForm()})

    def post(self, request):
        form = WorshipServiceImportForm(request.POST)
        action = request.POST.get("action", "preview")
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        raw_text = form.cleaned_data["raw_text"]
        model_hint = form.cleaned_data.get("model_hint", "")

        if action == "create":
            try:
                payload = json.loads(request.POST.get("parsed_payload", "{}"))
            except json.JSONDecodeError:
                payload = {}
        else:
            payload = generate_service_with_llm(raw_text, model_hint=model_hint)

        if action == "preview":
            context = {
                "form": form,
                "preview": payload,
                "parsed_payload": json.dumps(payload),
            }
            return render(request, self.template_name, context)

        if not payload.get("service_date"):
            messages.error(request, "A IA não conseguiu identificar a data. Ajuste o texto e tente novamente.")
            return render(request, self.template_name, {"form": form, "preview": payload, "parsed_payload": json.dumps(payload)})

        raw_date = payload["service_date"]
        service_date = raw_date if not isinstance(raw_date, str) else datetime.strptime(raw_date, "%Y-%m-%d").date()

        with transaction.atomic():
            service = WorshipService.objects.create(
                title=payload.get("title") or "Culto",
                service_kind=payload.get("service_kind") or WorshipService.KIND_REGULAR,
                service_date=service_date,
                leaders_text=_normalize_single_line(payload.get("leaders_text", "")),
                program_html=payload.get("program_html", ""),
                created_by=request.user,
            )

            for song in payload.get("songs", []):
                snapshot = song.get("song_snapshot", "").strip()
                if not snapshot:
                    continue
                resolution = resolve_song_reference(snapshot)
                WorshipServiceSong.objects.create(
                    service=service,
                    song=resolution["song"],
                    song_snapshot=snapshot,
                    source=WorshipServiceSong.SOURCE_IMPORTED,
                    order_ref=song.get("order_ref"),
                    resolution_status=resolution["resolution_status"],
                    detected_hymnal_raw=resolution["detected_hymnal_raw"],
                    detected_hymnal=resolution["detected_hymnal"],
                    detected_number=resolution["detected_number"],
                    match_confidence=resolution["match_confidence"],
                    resolution_note=resolution["resolution_note"],
                )

        messages.success(request, "Culto criado a partir da geração com IA.")
        return redirect("worship:service-detail", pk=service.pk)


class WorshipServicePrintView(WorshipAccessMixin, DetailView):
    template_name = "worship/service_print.html"
    model = WorshipService
    context_object_name = "service"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context_data = context_user_data(self.request)
        context["church_info"] = context_data.get("church_info", {})
        context["copies"] = [self.object]
        return context


class WorshipServicePdfView(WorshipAccessMixin, DetailView):
    model = WorshipService
    context_object_name = "service"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        layout = request.GET.get("layout", "1up")
        copies = [self.object]
        if layout == "2up":
            copies = [self.object, self.object]

        context_data = context_user_data(request)
        html = render_to_string(
            "worship/service_pdf.html",
            {
                "service": self.object,
                "copies": copies,
                "layout": layout,
                "church_info": context_data.get("church_info", {}),
            },
        )
        base_url = request.build_absolute_uri("/")
        pdf = weasyprint.HTML(string=html, base_url=base_url).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        suffix = "2up" if layout == "2up" else "1up"
        response["Content-Disposition"] = f"attachment; filename=programacao_culto_{self.object.pk}_{suffix}.pdf"
        return response
