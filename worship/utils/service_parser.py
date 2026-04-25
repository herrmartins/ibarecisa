import json
import re

import requests
from django.conf import settings


def generate_service_with_llm(raw_text, model_hint=""):
    raw_text = (raw_text or "").strip()
    if not raw_text:
        return _empty_payload()

    payload = _extract_with_llm(raw_text, model_hint=model_hint)
    if payload:
        return _normalize_payload(payload)
    return _empty_payload()


def _empty_payload():
    return {
        "title": "Culto",
        "service_date": None,
        "service_kind": "REGULAR",
        "leaders_text": "",
        "program_html": "<p>Programação não detectada.</p>",
        "songs": [],
        "confidence": 0.0,
        "source": "empty",
    }


def _extract_with_llm(raw_text, model_hint=""):
    api_key = getattr(settings, "MISTRAL_API_KEY", "")
    if not api_key:
        return None

    extra_hint = f"\nInstrução extra do usuário: {model_hint}" if model_hint else ""
    prompt = (
        "Converta o texto de programação de culto para JSON puro com este schema exato: "
        "{\"title\":\"\",\"service_date\":\"YYYY-MM-DD\",\"service_kind\":\"REGULAR|COMMUNION|CANTATA|SPECIAL\","
        "\"leaders_text\":\"\",\"program_html\":\"\",\"songs\":[{\"order_ref\":1,\"song_snapshot\":\"\"}]}. "
        "Regras: devolva somente JSON válido sem markdown; program_html deve conter HTML simples com <ol><li> para ordem."
        "Para leaders_text use formato curto: 'Dirigente: X / Regente: Y / Pianista: Z'."
        "Inclua em songs apenas canções/hinos realmente citados."
        f"{extra_hint}\nTexto:\n{raw_text}"
    )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": getattr(settings, "MISTRAL_MODEL", "mistral-small-latest"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    try:
        response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=data, timeout=40)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return _parse_json_content(content)
    except Exception:
        return None


def _parse_json_content(content):
    content = (content or "").strip()
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", content)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def _normalize_payload(payload):
    payload = payload or {}
    kind = str(payload.get("service_kind", "REGULAR")).upper().strip()
    if kind not in {"REGULAR", "COMMUNION", "CANTATA", "SPECIAL"}:
        kind = "REGULAR"

    songs = []
    for song in payload.get("songs", []):
        snapshot = str(song.get("song_snapshot", "")).strip()
        if not snapshot:
            continue
        try:
            order_ref = int(song.get("order_ref")) if song.get("order_ref") is not None else None
        except (TypeError, ValueError):
            order_ref = None
        songs.append({"order_ref": order_ref, "song_snapshot": snapshot})

    return {
        "title": str(payload.get("title", "Culto")).strip() or "Culto",
        "service_date": payload.get("service_date") or None,
        "service_kind": kind,
        "leaders_text": str(payload.get("leaders_text", "")).strip(),
        "program_html": str(payload.get("program_html", "")).strip() or "<p>Programação não detectada.</p>",
        "songs": songs,
        "confidence": 0.9,
        "source": "llm",
    }
