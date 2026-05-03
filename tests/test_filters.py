"""Tests for letter-bucket filtering, article stripping, and game-regex matching."""
import goglib
import pytest


class TestTitleFirstChar:
    """The title_first_char function determines a game's letter bucket."""

    @pytest.mark.parametrize("title,expected", [
        # Articles get stripped
        ("The Witcher 3: Wild Hunt", "w"),
        ("The Outer Worlds", "o"),
        ("The Dark Eye: Chains of Satinav", "d"),
        ("A Plague Tale: Innocence", "p"),
        ("An Elder Scrolls Legend: Battlespire", "e"),
        # No-article titles are unaffected
        ("Beyond a Steel Sky", "b"),
        ("Mafia: Definitive Edition", "m"),
        # Numbers bucket as 0-9
        ("7th Legion", "0-9"),
        ("9 Years of Shadows", "0-9"),
        ("1979 Revolution: Black Friday", "0-9"),
        # Punctuation/quotes prefix is skipped
        ('"Quoted Game"', "q"),
        ("...Hellish", "h"),
        # Empty/null fallback
        ("", "?"),
        # Special: 'A' as an article (must have following space) vs 'A' as content
        ("AI War: Fleet Command", "a"),  # 'AI' is content, not article
        ("A Bird Story", "b"),  # 'A ' is article
    ])
    def test_buckets(self, title, expected):
        assert goglib.title_first_char(title) == expected


class TestLetterToRegex:
    """letter_to_regex validates and normalizes the --letter input."""

    @pytest.mark.parametrize("letter,expected", [
        ("num", "0-9"),
        ("numeric", "0-9"),
        ("0-9", "0-9"),
        ("all", "*"),
        ("a", "a"),
        ("z", "z"),
        ("a-c", "a-c"),
        ("h-m", "h-m"),
    ])
    def test_valid(self, letter, expected):
        assert goglib.letter_to_regex(letter) == expected

    @pytest.mark.parametrize("bad", ["abc", "1", "a-", "-z", "9-z", "$"])
    def test_invalid_exits(self, bad):
        with pytest.raises(SystemExit):
            goglib.letter_to_regex(bad)


class TestMatchesLetterFilter:
    """matches_letter_filter combines title_first_char with the letter spec."""

    def _g(self, title, slug=None):
        return {"gamename": slug or title.lower().replace(" ", "_"), "title": title}

    def test_single_letter_match(self):
        assert goglib.matches_letter_filter(self._g("Mafia"), "m")
        assert not goglib.matches_letter_filter(self._g("Mafia"), "n")

    def test_article_strip_in_match(self):
        # "The Witcher" should match 'w', not 't'
        assert goglib.matches_letter_filter(self._g("The Witcher"), "w")
        assert not goglib.matches_letter_filter(self._g("The Witcher"), "t")

    def test_blackwell_via_episode_slug(self):
        # Real-world: GOG slug starts with 'episode_' but title is Blackwell
        g = self._g("Blackwell Legacy", slug="episode_1_the_blackwell_legacy")
        assert goglib.matches_letter_filter(g, "b")
        assert not goglib.matches_letter_filter(g, "e")

    def test_numeric_bucket(self):
        assert goglib.matches_letter_filter(self._g("7th Legion"), "0-9")
        assert not goglib.matches_letter_filter(self._g("7th Legion"), "s")

    def test_range(self):
        assert goglib.matches_letter_filter(self._g("Baldur's Gate"), "a-c")
        assert goglib.matches_letter_filter(self._g("Civilization"), "a-c")
        assert not goglib.matches_letter_filter(self._g("Doom"), "a-c")

    def test_all(self):
        assert goglib.matches_letter_filter(self._g("anything"), "*")
        assert goglib.matches_letter_filter(self._g(""), "*")
