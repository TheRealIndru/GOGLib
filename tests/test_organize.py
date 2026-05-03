"""Tests for filename rename, destination calculation, safe_dir, DLC handling."""
import goglib
import pytest
from pathlib import Path


class TestSafeDir:
    @pytest.mark.parametrize("inp,expected", [
        ("Witcher 3", "Witcher_3"),
        ("Heroes of Might and Magic", "Heroes_of_Might_and_Magic"),
        ("Game: Subtitle", "Game__Subtitle"),  # colon stripped
        ("Game/Sub", "Game_Sub"),  # slash stripped
        ('Game"Quote"', "Game_Quote_"),
        ("Game.", "Game"),  # trailing dot stripped
        ("Game ", "Game"),  # trailing whitespace stripped
        ("  spaces  ", "spaces"),
    ])
    def test_replace_spaces_true(self, inp, expected):
        assert goglib.safe_dir(inp, replace_spaces=True) == expected

    def test_replace_spaces_false_keeps_spaces(self):
        assert goglib.safe_dir("Witcher 3", replace_spaces=False) == "Witcher 3"


class TestRenameForTarget:
    """rename_for_target: strip 'setup_' prefix, optionally prefix DLC slug."""

    def _cfg(self, **overrides):
        cfg = {
            "filename_strip_prefix": "setup_",
            "filename_pattern": "{stripped}",
            "flatten_dlc_folder": True,
        }
        cfg.update(overrides)
        return cfg

    def test_strips_setup_prefix(self):
        assert goglib.rename_for_target(
            "setup_witcher_3_1.0.exe", self._cfg()) == "witcher_3_1.0.exe"

    def test_no_prefix_to_strip(self):
        # Extras don't have setup_; pass through
        assert goglib.rename_for_target(
            "manual_eng.zip", self._cfg()) == "manual_eng.zip"

    def test_dlc_prefix_added(self):
        # When the file belongs to a DLC and flatten_dlc_folder is on
        result = goglib.rename_for_target(
            "setup_hota_1.7.0.exe", self._cfg(),
            dlc_slug="heroes_of_might_and_magic_iii_horn_of_the_abyss")
        assert result == "heroes_of_might_and_magic_iii_horn_of_the_abyss__hota_1.7.0.exe"

    def test_dlc_prefix_skipped_when_flatten_off(self):
        result = goglib.rename_for_target(
            "setup_hota_1.7.0.exe",
            self._cfg(flatten_dlc_folder=False),
            dlc_slug="heroes_of_might_and_magic_iii_horn_of_the_abyss")
        assert result == "hota_1.7.0.exe"  # no DLC prefix

    def test_custom_pattern(self):
        cfg = self._cfg(filename_pattern="prefix-{stripped}")
        assert goglib.rename_for_target(
            "setup_x.exe", cfg) == "prefix-x.exe"


class TestDeriveKind:
    @pytest.mark.parametrize("rel,expected_kind", [
        ("", "installers"),
        (".", "installers"),
        ("extras", "extras"),
        ("extras/subfolder", "extras"),
        ("patches", "patches"),
        ("languagepacks", "languagepacks"),
        ("language_packs", "languagepacks"),  # underscore variant normalized
        ("dlc", "dlc"),
        ("unknown_subdir", "installers"),  # fallback
    ])
    def test_kind(self, rel, expected_kind):
        kind, _ = goglib.derive_kind(rel)
        assert kind == expected_kind


class TestTargetDirFor:
    """Destination is computed from franchise mapping + DLC status."""

    def _g(self, gamename, title=None, basegame=None):
        out = {"gamename": gamename, "title": title or gamename}
        if basegame:
            out["gamename_basegame"] = basegame
            out["title_basegame"] = basegame
        return out

    def _cfg(self):
        return {
            "dir_replace_spaces": True,
            "standalone_folder": "Standalone",
            "flatten_dlc_folder": True,
        }

    def test_standalone_no_franchise(self):
        game = self._g("7th_legion", "7th Legion")
        result = goglib.target_dir_for(
            game, {"7th_legion": game}, Path("/lib"), {}, self._cfg())
        assert result == Path("/lib/Standalone/7th_Legion")

    def test_with_franchise_and_year(self):
        game = self._g("homm3", "Heroes of Might and Magic 3")
        franchises = {
            "homm3": {
                "franchise": "Heroes of Might and Magic",
                "year": 1999,
                "title": "Heroes of Might and Magic 3 - Complete",
            }
        }
        result = goglib.target_dir_for(
            game, {"homm3": game}, Path("/lib"), franchises, self._cfg())
        assert result == Path(
            "/lib/Heroes_of_Might_and_Magic/1999_Heroes_of_Might_and_Magic_3_-_Complete")

    def test_dlc_under_base_with_flatten(self):
        base = self._g("homm3", "Heroes of Might and Magic 3")
        dlc = self._g("hota", "Horn of the Abyss", basegame="homm3")
        franchises = {
            "homm3": {"franchise": "Heroes of Might and Magic", "year": 1999,
                      "title": "Heroes of Might and Magic 3"}
        }
        result = goglib.target_dir_for(
            dlc, {"homm3": base, "hota": dlc}, Path("/lib"), franchises, self._cfg())
        # Flat: DLC files land directly in <base>/dlc/, no per-DLC folder
        assert result == Path(
            "/lib/Heroes_of_Might_and_Magic/1999_Heroes_of_Might_and_Magic_3/dlc")

    def test_dlc_unflatten(self):
        cfg = self._cfg()
        cfg["flatten_dlc_folder"] = False
        base = self._g("homm3", "Heroes of Might and Magic 3")
        dlc = self._g("hota", "Horn of the Abyss", basegame="homm3")
        franchises = {
            "homm3": {"franchise": "Heroes of Might and Magic", "year": 1999,
                      "title": "Heroes of Might and Magic 3"}
        }
        result = goglib.target_dir_for(
            dlc, {"homm3": base, "hota": dlc}, Path("/lib"), franchises, cfg)
        # When not flattened, DLC has its own subfolder named by DLC title
        assert result == Path(
            "/lib/Heroes_of_Might_and_Magic/1999_Heroes_of_Might_and_Magic_3/dlc/Horn_of_the_Abyss")

    def test_franchise_with_no_year(self):
        game = self._g("disco_elysium", "Disco Elysium")
        franchises = {"disco_elysium": {"franchise": "Disco Elysium"}}
        result = goglib.target_dir_for(
            game, {"disco_elysium": game}, Path("/lib"), franchises, self._cfg())
        # No year -> just the title
        assert result == Path("/lib/Disco_Elysium/Disco_Elysium")
