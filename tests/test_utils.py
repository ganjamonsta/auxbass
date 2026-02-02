"""
Tests for shared utilities
"""
import pytest
from shared.utils import (
    sanitize_input,
    normalize_artist,
    normalize_title,
    clean_for_search,
    fuzzy_match_artist,
    artists_match,
    format_duration,
    split_artists,
)
from shared.matching import extract_featured_artists


class TestSanitizeInput:
    """Tests for sanitize_input function"""
    
    def test_empty_string(self):
        assert sanitize_input("") == ""
    
    def test_none_value(self):
        assert sanitize_input(None) == ""
    
    def test_escapes_sql_wildcards(self):
        assert sanitize_input("test%value") == r"test\%value"
        assert sanitize_input("test_value") == r"test\_value"
    
    def test_truncates_long_input(self):
        long_input = "a" * 300
        result = sanitize_input(long_input)
        assert len(result) == 200
    
    def test_strips_whitespace(self):
        assert sanitize_input("  test  ") == "test"


class TestNormalizeArtist:
    """Tests for normalize_artist function"""
    
    def test_empty_string(self):
        assert normalize_artist("") == ""
    
    def test_lowercase(self):
        assert normalize_artist("ARTIST NAME") == "artist name"
    
    def test_removes_feat(self):
        assert normalize_artist("Artist feat. Other") == "artist"
        assert normalize_artist("Artist ft. Other") == "artist"
    
    def test_takes_first_from_collab(self):
        assert normalize_artist("Artist1 & Artist2") == "artist1"
        assert normalize_artist("Artist1, Artist2") == "artist1"


class TestNormalizeTitle:
    """Tests for normalize_title function"""
    
    def test_empty_string(self):
        assert normalize_title("") == ""
    
    def test_removes_remaster_suffix(self):
        assert normalize_title("Song (Remastered 2020)") == "song"
        assert normalize_title("Song [Remaster]") == "song"
    
    def test_removes_live_suffix(self):
        assert normalize_title("Song (Live)") == "song"
    
    def test_removes_remix_suffix(self):
        assert normalize_title("Song (Radio Edit)") == "song"


class TestFormatDuration:
    """Tests for format_duration function"""
    
    def test_zero_seconds(self):
        assert format_duration(0) == "0:00"
    
    def test_seconds_only(self):
        assert format_duration(45) == "0:45"
    
    def test_minutes_and_seconds(self):
        assert format_duration(125) == "2:05"
        assert format_duration(180) == "3:00"
    
    def test_over_one_hour(self):
        assert format_duration(3661) == "1:01:01"
    
    def test_none_returns_zero(self):
        assert format_duration(None) == "0:00"


class TestSplitArtists:
    """Tests for split_artists function"""
    
    def test_single_artist(self):
        assert split_artists("Artist") == ["Artist"]
    
    def test_feat_separator(self):
        result = split_artists("Artist1 feat. Artist2")
        assert "Artist1" in result
        assert "Artist2" in result
    
    def test_ampersand_separator(self):
        result = split_artists("Artist1 & Artist2")
        assert len(result) == 2
    
    def test_comma_separator(self):
        result = split_artists("Artist1, Artist2, Artist3")
        assert len(result) == 3


class TestFuzzyMatch:
    """Tests for fuzzy_match_artist function"""
    
    def test_exact_match(self):
        assert fuzzy_match_artist("test", "test") >= 0.9
    
    def test_case_insensitive(self):
        assert fuzzy_match_artist("Test", "TEST") >= 0.9
    
    def test_similar_match(self):
        assert fuzzy_match_artist("test", "testing") >= 0.5
    
    def test_no_match(self):
        assert fuzzy_match_artist("abc", "xyz") < 0.5


class TestArtistsMatch:
    """Tests for artists_match function"""
    
    def test_exact_match(self):
        assert artists_match("Artist", "Artist") == True
    
    def test_case_insensitive(self):
        assert artists_match("artist", "ARTIST") == True
    
    def test_with_feat(self):
        assert artists_match("Artist feat. Other", "Artist") == True
    
    def test_no_match(self):
        assert artists_match("Artist1", "Artist2") == False


class TestExtractFeaturedArtists:
    """Tests for extract_featured_artists function"""
    
    def test_remix_artist(self):
        """Should extract remix artist name"""
        result = extract_featured_artists("Track (Space Laces Remix)")
        assert result == ["Space Laces"]
    
    def test_original_mix_not_artist(self):
        """Original Mix should NOT create an artist named 'Original'"""
        result = extract_featured_artists("Track (Original Mix)")
        assert result == []
        assert "Original" not in result
    
    def test_radio_edit_not_artist(self):
        """Radio Edit should NOT create an artist named 'Radio'"""
        result = extract_featured_artists("Track (Radio Edit)")
        assert result == []
    
    def test_extended_mix_not_artist(self):
        """Extended Mix should NOT create an artist named 'Extended'"""
        result = extract_featured_artists("Track (Extended Mix)")
        assert result == []
    
    def test_club_mix_not_artist(self):
        """Club Mix should NOT create an artist named 'Club'"""
        result = extract_featured_artists("Track (Club Mix)")
        assert result == []
    
    def test_dub_mix_not_artist(self):
        """Dub Mix should NOT create an artist named 'Dub'"""
        result = extract_featured_artists("Track (Dub Mix)")
        assert result == []
    
    def test_instrumental_mix_not_artist(self):
        """Instrumental Mix should NOT create an artist named 'Instrumental'"""
        result = extract_featured_artists("Track (Instrumental Mix)")
        assert result == []
    
    def test_feat_artist(self):
        """Should extract featured artist"""
        result = extract_featured_artists("Track feat. Artist1")
        assert "Artist1" in result
    
    def test_feat_multiple_artists(self):
        """Should extract multiple featured artists"""
        result = extract_featured_artists("Track feat. Artist1 & Artist2")
        assert "Artist1" in result
        assert "Artist2" in result
    
    def test_prod_artist(self):
        """Should extract producer"""
        result = extract_featured_artists("Track (Prod. Producer)")
        assert "Producer" in result
    
    def test_vs_artist(self):
        """Should extract vs artist"""
        result = extract_featured_artists("Track vs. Other")
        assert "Other" in result
