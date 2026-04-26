import difflib
import re
import unicodedata

from worship.models import Hymnal, HymnalAlias, Song, WorshipServiceSong


HYMNAL_REF_RE = re.compile(
    r"\b(?P<hymnal>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-]{0,30})\s*(?:n[oº°]?\s*)?(?P<number>\d{1,4})\b",
    flags=re.IGNORECASE,
)


def normalize_token(value):
    value = (value or "").strip().lower()
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def extract_hymnal_reference(song_snapshot):
    text = (song_snapshot or "").strip()
    match = HYMNAL_REF_RE.search(text)
    if not match:
        return {"raw_hymnal": "", "number": None, "clean_snapshot": text}

    raw_hymnal = (match.group("hymnal") or "").strip()
    number = int(match.group("number")) if match.group("number") else None
    clean_snapshot = text.replace(match.group(0), "").strip(" -:;,.")
    clean_snapshot = clean_snapshot or text
    return {
        "raw_hymnal": raw_hymnal,
        "number": number,
        "clean_snapshot": clean_snapshot,
    }


def resolve_hymnal(raw_hymnal):
    raw_hymnal = (raw_hymnal or "").strip()
    if not raw_hymnal:
        return None

    normalized = normalize_token(raw_hymnal)
    aliases = {normalize_token(alias.alias): alias.hymnal for alias in HymnalAlias.objects.select_related("hymnal")}
    for hymnal in Hymnal.objects.all():
        aliases.setdefault(normalize_token(hymnal.title), hymnal)

    if normalized in aliases:
        return aliases[normalized]

    close = difflib.get_close_matches(normalized, list(aliases.keys()), n=1, cutoff=0.72)
    if close:
        return aliases[close[0]]
    return None


def find_song_candidates(snapshot, hymnal=None, number=None):
    snapshot = (snapshot or "").strip()
    if not snapshot:
        return Song.objects.none(), 0.0

    if hymnal and number:
        strict = Song.objects.filter(hymnal=hymnal, hymn_number=number)
        if strict.count() == 1:
            return strict, 1.0
        if strict.exists():
            return strict, 0.65

    direct = Song.objects.filter(title__icontains=snapshot[:80])
    if direct.count() == 1:
        return direct, 0.82

    return direct[:5], 0.55 if direct.exists() else 0.0


def resolve_song_reference(song_snapshot):
    parsed = extract_hymnal_reference(song_snapshot)
    hymnal = resolve_hymnal(parsed["raw_hymnal"])
    candidates, score = find_song_candidates(parsed["clean_snapshot"], hymnal, parsed["number"])
    selected = candidates.first() if candidates.exists() else None

    status = WorshipServiceSong.RESOLUTION_PENDING_REVIEW
    note = ""
    if selected and score >= 0.8:
        status = WorshipServiceSong.RESOLUTION_LINKED
    elif hymnal and normalize_token(hymnal.title) == "ha":
        status = WorshipServiceSong.RESOLUTION_UNLINKED
        note = "Origem detectada como hino avulso."

    if hymnal and parsed["number"] and not note:
        note = f"Origem detectada: {hymnal.title} {parsed['number']}"

    return {
        "song": selected,
        "resolution_status": status,
        "detected_hymnal_raw": parsed["raw_hymnal"],
        "detected_hymnal": hymnal,
        "detected_number": parsed["number"],
        "match_confidence": score if score > 0 else None,
        "resolution_note": note,
    }
