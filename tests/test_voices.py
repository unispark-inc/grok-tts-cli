"""Tests for voice definitions and metadata."""


from grok_tts_cli.voices import (
    SUPPORTED_LANGUAGES,
    VOICE_IDS,
    VOICES,
    Voice,
    get_voice,
)

# ============================================================================
# Voice Structure Tests
# ============================================================================


def test_all_voices_have_id():
    """Test that all voices have an ID."""
    for voice in VOICES:
        assert voice.id
        assert isinstance(voice.id, str)
        assert len(voice.id) > 0


def test_all_voices_have_name():
    """Test that all voices have a name."""
    for voice in VOICES:
        assert voice.name
        assert isinstance(voice.name, str)
        assert len(voice.name) > 0


def test_all_voices_have_gender():
    """Test that all voices have a gender."""
    for voice in VOICES:
        assert voice.gender
        assert isinstance(voice.gender, str)
        assert len(voice.gender) > 0


def test_all_voices_have_description():
    """Test that all voices have a description."""
    for voice in VOICES:
        assert voice.description
        assert isinstance(voice.description, str)
        assert len(voice.description) > 0


def test_voice_is_namedtuple():
    """Test that Voice is a NamedTuple."""
    voice = VOICES[0]
    assert isinstance(voice, Voice)
    assert isinstance(voice, tuple)


# ============================================================================
# Voice List Tests
# ============================================================================


def test_voices_list_is_not_empty():
    """Test that VOICES list is not empty."""
    assert len(VOICES) > 0


def test_voices_list_has_five_voices():
    """Test that VOICES list has exactly 5 voices."""
    assert len(VOICES) == 5


def test_expected_voices_present():
    """Test that expected voices are present."""
    expected_ids = {"eve", "ara", "rex", "sal", "leo"}
    actual_ids = {v.id for v in VOICES}
    assert actual_ids == expected_ids


def test_expected_voice_names():
    """Test that expected voice names are present."""
    expected_names = {"Eve", "Ara", "Rex", "Sal", "Leo"}
    actual_names = {v.name for v in VOICES}
    assert actual_names == expected_names


def test_voice_genders_are_valid():
    """Test that voice genders are from expected set."""
    valid_genders = {"Female", "Male", "Neutral"}
    for voice in VOICES:
        assert voice.gender in valid_genders


def test_eve_voice_definition():
    """Test Eve voice definition."""
    eve = get_voice("eve")
    assert eve is not None
    assert eve.id == "eve"
    assert eve.name == "Eve"
    assert eve.gender == "Female"
    assert eve.description == "Energetic"


def test_ara_voice_definition():
    """Test Ara voice definition."""
    ara = get_voice("ara")
    assert ara is not None
    assert ara.id == "ara"
    assert ara.name == "Ara"
    assert ara.gender == "Female"
    assert ara.description == "Warm"


def test_rex_voice_definition():
    """Test Rex voice definition."""
    rex = get_voice("rex")
    assert rex is not None
    assert rex.id == "rex"
    assert rex.name == "Rex"
    assert rex.gender == "Male"
    assert rex.description == "Confident"


def test_sal_voice_definition():
    """Test Sal voice definition."""
    sal = get_voice("sal")
    assert sal is not None
    assert sal.id == "sal"
    assert sal.name == "Sal"
    assert sal.gender == "Neutral"
    assert sal.description == "Smooth"


def test_leo_voice_definition():
    """Test Leo voice definition."""
    leo = get_voice("leo")
    assert leo is not None
    assert leo.id == "leo"
    assert leo.name == "Leo"
    assert leo.gender == "Male"
    assert leo.description == "Authoritative"


# ============================================================================
# VOICE_IDS Tests
# ============================================================================


def test_voice_ids_matches_voices():
    """Test that VOICE_IDS matches VOICES."""
    expected_ids = [v.id for v in VOICES]
    assert VOICE_IDS == expected_ids


def test_voice_ids_is_list():
    """Test that VOICE_IDS is a list."""
    assert isinstance(VOICE_IDS, list)


def test_voice_ids_length():
    """Test that VOICE_IDS has correct length."""
    assert len(VOICE_IDS) == 5


def test_voice_ids_contains_expected():
    """Test that VOICE_IDS contains expected IDs."""
    assert "eve" in VOICE_IDS
    assert "ara" in VOICE_IDS
    assert "rex" in VOICE_IDS
    assert "sal" in VOICE_IDS
    assert "leo" in VOICE_IDS


def test_no_duplicate_voice_ids():
    """Test that there are no duplicate voice IDs."""
    assert len(VOICE_IDS) == len(set(VOICE_IDS))


def test_voice_ids_are_lowercase():
    """Test that all voice IDs are lowercase."""
    for voice_id in VOICE_IDS:
        assert voice_id == voice_id.lower()


def test_voice_ids_are_alphanumeric():
    """Test that all voice IDs are alphanumeric."""
    for voice_id in VOICE_IDS:
        assert voice_id.isalnum()


# ============================================================================
# Supported Languages Tests
# ============================================================================


def test_supported_languages_is_list():
    """Test that SUPPORTED_LANGUAGES is a list."""
    assert isinstance(SUPPORTED_LANGUAGES, list)


def test_supported_languages_not_empty():
    """Test that SUPPORTED_LANGUAGES is not empty."""
    assert len(SUPPORTED_LANGUAGES) > 0


def test_supported_languages_has_twenty():
    """Test that SUPPORTED_LANGUAGES has 20 languages."""
    assert len(SUPPORTED_LANGUAGES) == 20


def test_supported_languages_are_strings():
    """Test that all supported languages are strings."""
    for lang in SUPPORTED_LANGUAGES:
        assert isinstance(lang, str)


def test_supported_languages_are_short_codes():
    """Test that all language codes are 2-3 characters."""
    for lang in SUPPORTED_LANGUAGES:
        assert 2 <= len(lang) <= 3


def test_supported_languages_are_lowercase():
    """Test that all language codes are lowercase."""
    for lang in SUPPORTED_LANGUAGES:
        assert lang == lang.lower()


def test_no_duplicate_languages():
    """Test that there are no duplicate language codes."""
    assert len(SUPPORTED_LANGUAGES) == len(set(SUPPORTED_LANGUAGES))


def test_english_supported():
    """Test that English is supported."""
    assert "en" in SUPPORTED_LANGUAGES


def test_spanish_supported():
    """Test that Spanish is supported."""
    assert "es" in SUPPORTED_LANGUAGES


def test_french_supported():
    """Test that French is supported."""
    assert "fr" in SUPPORTED_LANGUAGES


def test_german_supported():
    """Test that German is supported."""
    assert "de" in SUPPORTED_LANGUAGES


def test_italian_supported():
    """Test that Italian is supported."""
    assert "it" in SUPPORTED_LANGUAGES


def test_portuguese_supported():
    """Test that Portuguese is supported."""
    assert "pt" in SUPPORTED_LANGUAGES


def test_dutch_supported():
    """Test that Dutch is supported."""
    assert "nl" in SUPPORTED_LANGUAGES


def test_polish_supported():
    """Test that Polish is supported."""
    assert "pl" in SUPPORTED_LANGUAGES


def test_russian_supported():
    """Test that Russian is supported."""
    assert "ru" in SUPPORTED_LANGUAGES


def test_turkish_supported():
    """Test that Turkish is supported."""
    assert "tr" in SUPPORTED_LANGUAGES


def test_chinese_supported():
    """Test that Chinese is supported."""
    assert "zh" in SUPPORTED_LANGUAGES


def test_japanese_supported():
    """Test that Japanese is supported."""
    assert "ja" in SUPPORTED_LANGUAGES


def test_korean_supported():
    """Test that Korean is supported."""
    assert "ko" in SUPPORTED_LANGUAGES


def test_arabic_supported():
    """Test that Arabic is supported."""
    assert "ar" in SUPPORTED_LANGUAGES


def test_hindi_supported():
    """Test that Hindi is supported."""
    assert "hi" in SUPPORTED_LANGUAGES


def test_indonesian_supported():
    """Test that Indonesian is supported."""
    assert "id" in SUPPORTED_LANGUAGES


def test_malay_supported():
    """Test that Malay is supported."""
    assert "ms" in SUPPORTED_LANGUAGES


def test_thai_supported():
    """Test that Thai is supported."""
    assert "th" in SUPPORTED_LANGUAGES


def test_vietnamese_supported():
    """Test that Vietnamese is supported."""
    assert "vi" in SUPPORTED_LANGUAGES


def test_filipino_supported():
    """Test that Filipino is supported."""
    assert "fil" in SUPPORTED_LANGUAGES


# ============================================================================
# get_voice() Function Tests
# ============================================================================


def test_get_voice_returns_correct_voice():
    """Test that get_voice returns correct voice."""
    for voice in VOICES:
        result = get_voice(voice.id)
        assert result == voice


def test_get_voice_eve():
    """Test get_voice for eve."""
    voice = get_voice("eve")
    assert voice is not None
    assert voice.id == "eve"


def test_get_voice_ara():
    """Test get_voice for ara."""
    voice = get_voice("ara")
    assert voice is not None
    assert voice.id == "ara"


def test_get_voice_rex():
    """Test get_voice for rex."""
    voice = get_voice("rex")
    assert voice is not None
    assert voice.id == "rex"


def test_get_voice_sal():
    """Test get_voice for sal."""
    voice = get_voice("sal")
    assert voice is not None
    assert voice.id == "sal"


def test_get_voice_leo():
    """Test get_voice for leo."""
    voice = get_voice("leo")
    assert voice is not None
    assert voice.id == "leo"


def test_get_voice_invalid_returns_none():
    """Test that get_voice returns None for invalid ID."""
    assert get_voice("invalid") is None


def test_get_voice_empty_string_returns_none():
    """Test that get_voice returns None for empty string."""
    assert get_voice("") is None


def test_get_voice_uppercase_returns_none():
    """Test that get_voice is case-sensitive."""
    assert get_voice("EVE") is None
    assert get_voice("Rex") is None


def test_get_voice_partial_match_returns_none():
    """Test that get_voice doesn't do partial matching."""
    assert get_voice("ev") is None
    assert get_voice("re") is None


def test_get_voice_with_spaces_returns_none():
    """Test that get_voice returns None for IDs with spaces."""
    assert get_voice("eve ") is None
    assert get_voice(" eve") is None


# ============================================================================
# Data Integrity Tests
# ============================================================================


def test_voice_ids_match_in_voices_list():
    """Test that voice IDs in VOICES match their ID field."""
    for voice in VOICES:
        # Voice ID should match the ID in the Voice object
        assert voice.id in VOICE_IDS


def test_voices_list_order_matches_voice_ids():
    """Test that VOICES list order matches VOICE_IDS order."""
    for i, voice in enumerate(VOICES):
        assert voice.id == VOICE_IDS[i]


def test_no_none_values_in_voices():
    """Test that no voice has None values."""
    for voice in VOICES:
        assert voice.id is not None
        assert voice.name is not None
        assert voice.gender is not None
        assert voice.description is not None


def test_voice_ids_are_unique():
    """Test that all voice IDs are unique."""
    ids = [v.id for v in VOICES]
    assert len(ids) == len(set(ids))


def test_voice_names_are_unique():
    """Test that all voice names are unique."""
    names = [v.name for v in VOICES]
    assert len(names) == len(set(names))


def test_voice_descriptions_are_unique():
    """Test that all voice descriptions are unique."""
    descriptions = [v.description for v in VOICES]
    assert len(descriptions) == len(set(descriptions))


def test_voice_id_name_consistency():
    """Test that voice ID and name are consistent."""
    for voice in VOICES:
        # Name should be capitalized version of ID
        assert voice.name.lower() == voice.id.lower()


def test_supported_languages_coverage():
    """Test that supported languages cover major regions."""
    # Should have European languages
    european = ["en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "tr"]
    for lang in european:
        assert lang in SUPPORTED_LANGUAGES

    # Should have Asian languages
    asian = ["zh", "ja", "ko", "ar", "hi", "id", "ms", "th", "vi", "fil"]
    for lang in asian:
        assert lang in SUPPORTED_LANGUAGES
