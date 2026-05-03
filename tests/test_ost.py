"""Tests for OST format detection (filename heuristics for FLAC > WAV > MP3 priority)."""
import goglib
import pytest


class TestDetectOstFormat:
    @pytest.mark.parametrize("filename,expected", [
        # Format clearly identifiable
        ("game_ost_flac.zip", (True, "flac")),
        ("game_ost_mp3.zip", (True, "mp3")),
        ("game_ost_wav.zip", (True, "wav")),
        ("soundtrack_flac.zip", (True, "flac")),
        ("game_music_flac.zip", (True, "flac")),
        # OST present but format unclear (don't filter)
        ("7th_legion_ost.zip", (True, None)),
        # Direct file extensions
        ("game_ost.flac", (True, "flac")),
        ("game_ost.mp3", (True, "mp3")),
        # Not OST
        ("game_manual_eng.zip", (False, None)),
        ("setup_witcher_3_1.0.exe", (False, None)),
        # 'ost' substring but NOT as token boundary
        ("postal_classic.exe", (False, None)),
        ("cost_of_war.zip", (False, None)),
        # 'music' as a token should count
        ("game_music.zip", (True, None)),
    ])
    def test_detection(self, filename, expected):
        assert goglib.detect_ost_format(filename) == expected


class TestBuildOstBlacklist:
    """Per-game blacklist generation: when multiple OST formats exist, blacklist
    the lower-priority ones."""

    def test_no_ost_returns_empty(self):
        game = {
            "gamename": "x",
            "extras": [{"path": "manual.pdf", "size": 100}],
        }
        assert goglib.build_ost_blacklist_for_game(game, ["flac", "wav", "mp3"]) == []

    def test_single_format_no_filtering(self):
        # Only mp3 available — keep it
        game = {
            "gamename": "x",
            "extras": [{"path": "x_ost_mp3.zip", "size": 100}],
        }
        assert goglib.build_ost_blacklist_for_game(game, ["flac", "wav", "mp3"]) == []

    def test_three_formats_keeps_flac(self):
        # All three formats present — keep flac, blacklist wav and mp3
        game = {
            "gamename": "x",
            "extras": [
                {"path": "x_ost_flac.zip", "size": 1000},
                {"path": "x_ost_wav.zip", "size": 800},
                {"path": "x_ost_mp3.zip", "size": 200},
            ],
        }
        patterns = goglib.build_ost_blacklist_for_game(game, ["flac", "wav", "mp3"])
        assert len(patterns) == 2
        joined = " ".join(patterns)
        assert "wav" in joined
        assert "mp3" in joined
        assert "flac" not in joined

    def test_two_formats_keeps_higher_priority(self):
        # Only wav and mp3 — keep wav, blacklist mp3
        game = {
            "gamename": "x",
            "extras": [
                {"path": "x_ost_wav.zip", "size": 800},
                {"path": "x_ost_mp3.zip", "size": 200},
            ],
        }
        patterns = goglib.build_ost_blacklist_for_game(game, ["flac", "wav", "mp3"])
        assert len(patterns) == 1
        assert "mp3" in patterns[0]

    def test_empty_priority_disables(self):
        game = {
            "gamename": "x",
            "extras": [
                {"path": "x_ost_flac.zip", "size": 1000},
                {"path": "x_ost_mp3.zip", "size": 200},
            ],
        }
        assert goglib.build_ost_blacklist_for_game(game, []) == []
