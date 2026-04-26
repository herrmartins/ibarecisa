from django.test import TestCase
from model_bakery import baker

from worship.models import Hymnal, HymnalAlias, Song, WorshipServiceSong
from worship.utils.song_resolution import (
    extract_hymnal_reference,
    find_song_candidates,
    normalize_token,
    resolve_hymnal,
    resolve_song_reference,
)


class NormalizeTokenTestCase(TestCase):
    def test_strips_and_lowers(self):
        self.assertEqual(normalize_token("  HCC  "), "hcc")

    def test_removes_accents(self):
        self.assertEqual(normalize_token("Hinário Para o Culto Cristão"), "hinarioparaocultocristao")

    def test_removes_special_chars(self):
        self.assertEqual(normalize_token("Cantor Cristão"), "cantorcristao")

    def test_empty_string(self):
        self.assertEqual(normalize_token(""), "")

    def test_none(self):
        self.assertEqual(normalize_token(None), "")


class ExtractHymnalReferenceTestCase(TestCase):
    def test_cc_with_number_and_title(self):
        result = extract_hymnal_reference("CC 291 - A Deus demos glória")
        self.assertEqual(result["raw_hymnal"], "CC")
        self.assertEqual(result["number"], 291)
        self.assertIn("A Deus demos glória", result["clean_snapshot"])

    def test_hcc_with_number(self):
        result = extract_hymnal_reference("HCC 123")
        self.assertEqual(result["raw_hymnal"], "HCC")
        self.assertEqual(result["number"], 123)

    def test_ha_with_n_symbol(self):
        result = extract_hymnal_reference("HA nº 78")
        self.assertEqual(result["raw_hymnal"], "HA")
        self.assertEqual(result["number"], 78)

    def test_vm_without_space(self):
        result = extract_hymnal_reference("VM 42 Vencendo vem Jesus")
        self.assertEqual(result["raw_hymnal"], "VM")
        self.assertEqual(result["number"], 42)

    def test_no_reference(self):
        result = extract_hymnal_reference("Louvai a Deus")
        self.assertEqual(result["raw_hymnal"], "")
        self.assertIsNone(result["number"])
        self.assertEqual(result["clean_snapshot"], "Louvai a Deus")

    def test_empty_string(self):
        result = extract_hymnal_reference("")
        self.assertEqual(result["raw_hymnal"], "")
        self.assertIsNone(result["number"])

    def test_none(self):
        result = extract_hymnal_reference(None)
        self.assertEqual(result["raw_hymnal"], "")


class ResolveHymnalTestCase(TestCase):
    def setUp(self):
        self.hcc = Hymnal.objects.create(title="Hinário Para o Culto Cristão")
        HymnalAlias.objects.create(hymnal=self.hcc, alias="HCC")
        self.cc = Hymnal.objects.create(title="Cantor Cristão")
        HymnalAlias.objects.create(hymnal=self.cc, alias="CC")
        self.ha = Hymnal.objects.create(title="Hinos Avulsos")
        HymnalAlias.objects.create(hymnal=self.ha, alias="HA")

    def test_exact_alias_match(self):
        self.assertEqual(resolve_hymnal("HCC"), self.hcc)
        self.assertEqual(resolve_hymnal("CC"), self.cc)

    def test_case_insensitive(self):
        self.assertEqual(resolve_hymnal("hcc"), self.hcc)
        self.assertEqual(resolve_hymnal("cc"), self.cc)

    def test_fuzzy_match(self):
        result = resolve_hymnal("Cantor Cristão")
        self.assertIsNotNone(result)

    def test_no_match(self):
        self.assertIsNone(resolve_hymnal("XYZINEXISTENTE"))

    def test_empty_string(self):
        self.assertIsNone(resolve_hymnal(""))

    def test_none(self):
        self.assertIsNone(resolve_hymnal(None))

    def test_title_match_without_alias(self):
        ha = Hymnal.objects.create(title="Hinário Único Sem Alias")
        result = resolve_hymnal("Hinário Único Sem Alias")
        self.assertEqual(result, ha)


class FindSongCandidatesTestCase(TestCase):
    def setUp(self):
        self.hcc = Hymnal.objects.create(title="HCC")
        self.cc = Hymnal.objects.create(title="CC")
        self.song1 = Song.objects.create(title="A Deus demos glória", hymnal=self.cc, hymn_number=291)
        self.song2 = Song.objects.create(title="Vencendo vem Jesus", hymnal=self.hcc, hymn_number=123)

    def test_exact_hymnal_number_unique(self):
        qs, score = find_song_candidates("A Deus demos glória", self.cc, 291)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(score, 1.0)
        self.assertEqual(qs.first(), self.song1)

    def test_exact_hymnal_number_multiple(self):
        Song.objects.create(title="Outro Hino 291", hymnal=self.cc, hymn_number=291)
        qs, score = find_song_candidates("glória", self.cc, 291)
        self.assertEqual(qs.count(), 2)
        self.assertEqual(score, 0.65)

    def test_title_match_unique(self):
        qs, score = find_song_candidates("Vencendo vem Jesus")
        self.assertEqual(qs.count(), 1)
        self.assertEqual(score, 0.82)

    def test_title_match_multiple(self):
        Song.objects.create(title="Vencendo vem Jesus (reprise)")
        qs, score = find_song_candidates("Vencendo")
        self.assertTrue(qs.exists())
        self.assertEqual(score, 0.55)

    def test_no_match(self):
        qs, score = find_song_candidates("XYZINEXISTENTE123456")
        self.assertFalse(qs.exists())
        self.assertEqual(score, 0.0)

    def test_empty_snapshot(self):
        qs, score = find_song_candidates("")
        self.assertFalse(qs.exists())
        self.assertEqual(score, 0.0)

    def test_none_snapshot(self):
        qs, score = find_song_candidates(None)
        self.assertFalse(qs.exists())
        self.assertEqual(score, 0.0)


class ResolveSongReferenceTestCase(TestCase):
    def setUp(self):
        self.hcc = Hymnal.objects.create(title="HCC")
        HymnalAlias.objects.create(hymnal=self.hcc, alias="HCC")
        self.cc = Hymnal.objects.create(title="CC")
        HymnalAlias.objects.create(hymnal=self.cc, alias="CC")
        self.ha = Hymnal.objects.create(title="HA")
        HymnalAlias.objects.create(hymnal=self.ha, alias="HA")
        self.song_cc291 = Song.objects.create(
            title="A Deus demos glória", hymnal=self.cc, hymn_number=291
        )
        self.song_hcc123 = Song.objects.create(
            title="Vencendo vem Jesus", hymnal=self.hcc, hymn_number=123
        )

    def test_linked_when_exact_match(self):
        result = resolve_song_reference("CC 291 - A Deus demos glória")
        self.assertEqual(result["song"], self.song_cc291)
        self.assertEqual(result["resolution_status"], WorshipServiceSong.RESOLUTION_LINKED)
        self.assertEqual(result["match_confidence"], 1.0)

    def test_linked_when_title_unique_match(self):
        result = resolve_song_reference("Vencendo vem Jesus")
        self.assertEqual(result["song"], self.song_hcc123)
        self.assertEqual(result["resolution_status"], WorshipServiceSong.RESOLUTION_LINKED)

    def test_unlinked_when_ha_detected(self):
        result = resolve_song_reference("HA 42")
        self.assertEqual(result["resolution_status"], WorshipServiceSong.RESOLUTION_UNLINKED)
        self.assertEqual(result["detected_hymnal"], self.ha)
        self.assertIn("avulso", result["resolution_note"].lower())

    def test_pending_when_low_confidence(self):
        result = resolve_song_reference("XYZINEXISTENTE99999")
        self.assertEqual(result["resolution_status"], WorshipServiceSong.RESOLUTION_PENDING_REVIEW)
        self.assertIsNone(result["song"])

    def test_detected_hymnal_raw_preserved(self):
        result = resolve_song_reference("HCC 123 - Vencendo")
        self.assertEqual(result["detected_hymnal_raw"], "HCC")
        self.assertEqual(result["detected_hymnal"], self.hcc)
        self.assertEqual(result["detected_number"], 123)

    def test_note_with_hymnal_and_number(self):
        result = resolve_song_reference("HCC 123")
        self.assertIn("HCC", result["resolution_note"])
        self.assertIn("123", result["resolution_note"])

    def test_no_match_returns_none_song(self):
        result = resolve_song_reference("ZZZZZ")
        self.assertIsNone(result["song"])

    def test_confidence_null_when_no_candidates(self):
        result = resolve_song_reference("ZZZZZ98765")
        self.assertIsNone(result["match_confidence"])
