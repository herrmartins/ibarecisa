from __future__ import annotations

import re
import sqlite3
from pathlib import Path
import xml.etree.ElementTree as ET

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from worship.models import Composer, Hymnal, HymnalAlias, Song, SongTheme


KNOWN_HYMNAL_NAMES = {
    "hc": "Harpa Crista",
    "hcc": "Hinario Para o Culto Cristao",
    "cc": "Cantor Cristao",
}


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _safe_int(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    digits = re.sub(r"\D+", "", str(value))
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _extract_number_from_title(title: str) -> int | None:
    match = re.search(r"\b(?:HC|HCC|CC)?\s*0*(\d{1,4})\b", title or "", flags=re.IGNORECASE)
    if not match:
        return None
    return _safe_int(match.group(1))


def _clean_title(raw_title: str, hymn_number: int | None) -> str:
    title = _normalize_spaces(raw_title)
    title = re.sub(r"^\s*(HC|HCC|CC)\s*[- ]?\s*0*\d{1,4}\s*[-:]?\s*", "", title, flags=re.IGNORECASE)
    if hymn_number is not None:
        title = re.sub(r"^\s*0*%s\s*[-:]?\s*" % hymn_number, "", title)
    return _normalize_spaces(title)


def _lyrics_to_text(raw_lyrics: str) -> str:
    if not raw_lyrics:
        return ""

    raw_lyrics = raw_lyrics.strip()
    if not raw_lyrics.startswith("<?xml") and "<song" not in raw_lyrics:
        plain = raw_lyrics.replace("\r", "")
        plain = re.sub(r"\[\s*-{2,}\s*\]", "", plain)
        plain = re.sub(r"\n{3,}", "\n\n", plain)
        return plain.strip()

    try:
        root = ET.fromstring(raw_lyrics)
    except ET.ParseError:
        return raw_lyrics

    verses = []
    for verse in root.findall(".//verse"):
        verse_type = (verse.attrib.get("type") or "").lower()
        label = _normalize_spaces(verse.attrib.get("label") or "")
        body = _normalize_spaces(verse.text or "")
        body = re.sub(r"\[\s*-{2,}\s*\]", "", body)
        if not body:
            continue

        if verse_type == "c":
            header = f"Coro {label}".strip()
        else:
            header = f"Verso {label}".strip()
        verses.append(f"{header}\n{body}")

    return "\n\n".join(verses) if verses else raw_lyrics


def _discover_hymnal_name(conn: sqlite3.Connection, db_path: Path) -> str:
    cursor = conn.cursor()
    try:
        row = cursor.execute("SELECT name FROM song_books ORDER BY id LIMIT 1").fetchone()
    except sqlite3.OperationalError:
        row = None

    if row and row[0]:
        return _normalize_spaces(str(row[0]))

    key = db_path.stem.lower()
    return KNOWN_HYMNAL_NAMES.get(key, db_path.stem.upper())


def _discover_hymnal_aliases(db_path: Path, hymnal_name: str) -> list[str]:
    aliases = {db_path.stem.upper(), _normalize_spaces(hymnal_name)}
    if db_path.stem.lower() in KNOWN_HYMNAL_NAMES:
        aliases.add(db_path.stem.upper())
    return sorted(alias for alias in aliases if alias)


class Command(BaseCommand):
    help = "Importa cancoes de bancos SQLite externos (OpenLP) para o worship.Song."

    def add_arguments(self, parser):
        parser.add_argument(
            "db_paths",
            nargs="+",
            help="Caminhos para os .sqlite/.db de origem (ex: hc.sqlite hcc.sqlite cc.sqlite)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra o que seria importado sem gravar no banco.",
        )
        parser.add_argument(
            "--replace-lyrics",
            action="store_true",
            help="Atualiza letra de cancoes ja existentes quando houver match por hinario+numero.",
        )
        parser.add_argument(
            "--update-title",
            action="store_true",
            help="Atualiza titulo de cancoes existentes quando houver match por hinario+numero.",
        )
        parser.add_argument(
            "--reset-catalog",
            action="store_true",
            help="Apaga cancoes, compositores, temas, hinarios e aliases do modulo worship antes de importar.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Confirma operacao destrutiva quando usado com --reset-catalog.",
        )

    def handle(self, *args, **options):
        db_paths = [Path(path) for path in options["db_paths"]]
        dry_run = options["dry_run"]
        replace_lyrics = options["replace_lyrics"]
        update_title = options["update_title"]
        reset_catalog = options["reset_catalog"]
        confirmed = options["yes"]
        ignore_existing = bool(reset_catalog and dry_run)

        if reset_catalog and not confirmed:
            raise CommandError("Use --yes junto com --reset-catalog para confirmar a limpeza.")

        for db_path in db_paths:
            if not db_path.exists():
                raise CommandError(f"Arquivo nao encontrado: {db_path}")

        if reset_catalog:
            self._reset_catalog(dry_run=dry_run)

        created_total = 0
        updated_total = 0
        skipped_total = 0

        for db_path in db_paths:
            created, updated, skipped = self._import_one_database(
                db_path=db_path,
                dry_run=dry_run,
                replace_lyrics=replace_lyrics,
                update_title=update_title,
                ignore_existing=ignore_existing,
            )
            created_total += created
            updated_total += updated
            skipped_total += skipped

        self.stdout.write(self.style.SUCCESS("Importacao finalizada."))
        self.stdout.write(f"Criadas: {created_total}")
        self.stdout.write(f"Atualizadas: {updated_total}")
        self.stdout.write(f"Ignoradas: {skipped_total}")

    def _reset_catalog(self, dry_run: bool):
        self.stdout.write(self.style.WARNING("Limpando catalogo worship antes da importacao..."))
        if dry_run:
            song_count = Song.objects.count()
            hymnals_count = Hymnal.objects.count()
            composers_count = Composer.objects.count()
            themes_count = SongTheme.objects.count()
            aliases_count = HymnalAlias.objects.count()
            self.stdout.write(
                f"[dry-run] Seriam removidos: songs={song_count}, hymnals={hymnals_count}, aliases={aliases_count}, composers={composers_count}, themes={themes_count}"
            )
            return

        with transaction.atomic():
            Song.objects.all().delete()
            HymnalAlias.objects.all().delete()
            Hymnal.objects.all().delete()
            Composer.objects.all().delete()
            SongTheme.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Catalogo worship limpo."))

    def _import_one_database(
        self,
        db_path: Path,
        dry_run: bool,
        replace_lyrics: bool,
        update_title: bool,
        ignore_existing: bool = False,
    ) -> tuple[int, int, int]:
        self.stdout.write(f"\nProcessando: {db_path}")
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        hymnal_name = _discover_hymnal_name(conn, db_path)
        hymnal_aliases = _discover_hymnal_aliases(db_path, hymnal_name)

        if dry_run:
            hymnal = Hymnal(title=hymnal_name)
        else:
            hymnal, _ = Hymnal.objects.get_or_create(title=hymnal_name)
            for alias in hymnal_aliases:
                HymnalAlias.objects.get_or_create(alias=alias, defaults={"hymnal": hymnal})

        songs_rows = conn.execute("SELECT * FROM songs ORDER BY id").fetchall()
        if not songs_rows:
            self.stdout.write(self.style.WARNING("Nenhuma cancao encontrada neste arquivo."))
            return 0, 0, 0

        created = 0
        updated = 0
        skipped = 0

        context = transaction.atomic if not dry_run else _dummy_context
        with context():
            for row in songs_rows:
                source_title = _normalize_spaces(row["title"])
                raw_number = row["song_number"] if "song_number" in row.keys() else None
                hymn_number = _safe_int(raw_number) or _extract_number_from_title(source_title)
                title = _clean_title(source_title, hymn_number)
                if not title:
                    title = source_title

                lyrics = _lyrics_to_text(row["lyrics"] if "lyrics" in row.keys() else "")
                theme_name = _normalize_spaces(row["theme_name"] if "theme_name" in row.keys() else "")
                composer_name = self._get_composer_name(conn, row["id"])

                theme = None
                if theme_name and not dry_run:
                    theme, _ = SongTheme.objects.get_or_create(title=theme_name)

                composer = None
                if composer_name and not dry_run:
                    composer, _ = Composer.objects.get_or_create(name=composer_name)

                song = None if ignore_existing else self._find_existing_song(hymnal, hymn_number, title)
                if song:
                    changed = False
                    if replace_lyrics and lyrics and song.lyrics != lyrics:
                        song.lyrics = lyrics
                        changed = True
                    if update_title and title and song.title != title:
                        song.title = title
                        changed = True
                    if composer and song.artist_id != composer.id:
                        song.artist = composer
                        changed = True
                    if theme and not dry_run and not song.themes.filter(pk=theme.pk).exists():
                        if not changed:
                            song.save()
                        song.themes.add(theme)

                    if changed and not dry_run:
                        song.save()
                        updated += 1
                    else:
                        skipped += 1
                    continue

                if dry_run:
                    created += 1
                    continue

                song = Song.objects.create(
                    title=title,
                    artist=composer,
                    lyrics=lyrics,
                    hymnal=hymnal,
                    hymn_number=hymn_number,
                )
                if theme:
                    song.themes.add(theme)
                created += 1

        conn.close()
        self.stdout.write(
            self.style.SUCCESS(
                f"{db_path.name}: criadas={created}, atualizadas={updated}, ignoradas={skipped}, hinario='{hymnal_name}'"
            )
        )
        if hymnal_aliases:
            self.stdout.write(f"Aliases: {', '.join(hymnal_aliases)}")
        return created, updated, skipped

    @staticmethod
    def _get_composer_name(conn: sqlite3.Connection, source_song_id: int) -> str:
        query = (
            "SELECT a.display_name "
            "FROM authors a "
            "INNER JOIN authors_songs rel ON rel.author_id = a.id "
            "WHERE rel.song_id = ? "
            "ORDER BY a.id LIMIT 1"
        )
        row = conn.execute(query, [source_song_id]).fetchone()
        if not row:
            return ""
        return _normalize_spaces(row[0] or "")

    @staticmethod
    def _find_existing_song(hymnal: Hymnal, hymn_number: int | None, title: str) -> Song | None:
        hymnal_filter = {"hymnal": hymnal} if hymnal.pk else {"hymnal__title": hymnal.title}

        if hymn_number is not None:
            by_ref = Song.objects.filter(hymn_number=hymn_number, **hymnal_filter).order_by("id").first()
            if by_ref:
                return by_ref
        return Song.objects.filter(title__iexact=title, **hymnal_filter).order_by("id").first()


class _dummy_context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
