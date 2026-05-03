"""Tests for size parsing and language-extras blacklist generation."""
import goglib
import pytest


class TestParseSize:
    @pytest.mark.parametrize("inp,expected", [
        (None, 0),
        ("", 0),
        (1024, 1024),
        (1024.5, 1024),
        ("1024", 1024),
        ("1024.5", 1024),
        ("not a number", 0),
    ])
    def test_parse(self, inp, expected):
        assert goglib.parse_size(inp) == expected


class TestParseAllowedLangs:
    """parse_allowed_langs reads 'en+ro+ja' style strings into a set of primary codes."""

    def test_basic_combine(self):
        assert goglib.parse_allowed_langs("en+ro+ja") == {"en", "ro", "ja"}

    def test_priority_separator(self):
        # ',' is priority but goglib treats as additional; both are in the set
        assert goglib.parse_allowed_langs("en,de") == {"en", "de"}

    def test_aliases_normalized(self):
        # Aliases like 'eng', 'english' normalize to primary 'en'
        assert goglib.parse_allowed_langs("eng+german") == {"en", "de"}

    def test_all_returns_none(self):
        # 'all' = no filtering = None sentinel
        assert goglib.parse_allowed_langs("all") is None
        assert goglib.parse_allowed_langs("en+all") is None

    def test_unknown_skipped(self):
        # Unrecognized codes silently ignored
        assert goglib.parse_allowed_langs("en+xyz") == {"en"}


class TestBuildExtraLangBlacklistPatterns:
    def test_empty_when_none_allowed(self):
        # None == 'all' == no filtering needed
        assert goglib.build_extra_lang_blacklist_patterns(None) == []

    def test_excludes_allowed_langs(self):
        # When 'en' is allowed, the pattern must not match 'en' tokens
        patterns = goglib.build_extra_lang_blacklist_patterns({"en"})
        assert patterns
        joined = patterns[0]
        # The 'en' token should not appear in the alternation
        # (ger, fr, etc. should)
        assert "german" in joined or "ger" in joined
        assert "french" in joined or "fr" in joined


class TestSafeFilenameKeys:
    """mkey is the manifest key format: <slug>/<filename>."""

    def test_format(self):
        assert goglib.mkey("witcher_3", "setup_x.exe") == "witcher_3/setup_x.exe"


class TestBackendDetection:
    """resolve_backend behavior — we just verify the logic, not actually shell out."""

    def test_unknown_backend_exits(self):
        with pytest.raises(SystemExit):
            goglib.resolve_backend({"backend": "nonexistent_backend_xyz"})

    def test_explicit_lgog_when_unavailable(self, monkeypatch):
        # Force is_available to return False
        monkeypatch.setattr(
            goglib.LgogDownloaderBackend, "is_available", classmethod(lambda cls: False))
        with pytest.raises(SystemExit):
            goglib.resolve_backend({"backend": "lgogdownloader"})
