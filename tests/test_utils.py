"""
Tests for shared utilities
"""
import pytest
from shared.utils import (
    sanitize_input,
    normalize_artist,
    normalize_title,
    clean_search_string,
    fuzzy_match_strings,
    artist_matches,
    format_duration,
    split_artists,
)


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


class TestFuzzyMatchStrings:
    """Tests for fuzzy_match_strings function"""
    
    def test_exact_match(self):
        assert fuzzy_match_strings("test", "test") == True
    
    def test_case_insensitive(self):
        assert fuzzy_match_strings("Test", "TEST") == True
    
    def test_partial_match(self):
        assert fuzzy_match_strings("test", "testing") == True
    
    def test_no_match(self):
        assert fuzzy_match_strings("abc", "xyz") == False


class TestArtistMatches:
    """Tests for artist_matches function"""
    
    def test_exact_match(self):
        assert artist_matches("Artist", "Artist") == True
    
    def test_case_insensitive(self):
        assert artist_matches("artist", "ARTIST") == True
    
    def test_with_feat(self):
        assert artist_matches("Artist feat. Other", "Artist") == True
    
    def test_no_match(self):
        assert artist_matches("Artist1", "Artist2") == False
