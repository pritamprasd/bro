"""Unit tests for Text-to-Speech markdown text cleaning."""

from jarvis.config import VoiceConfig
from jarvis.voice.tts import TextToSpeech

def test_clean_for_speech_bold_words():
    tts = TextToSpeech(VoiceConfig(enabled=False))
    # Test bold with asterisks and underscores
    assert tts._clean_for_speech("The **cat** is on the mat.") == "The cat is on the mat."
    assert tts._clean_for_speech("The __dog__ barked.") == "The dog barked."
    assert tts._clean_for_speech("**Important notice:** Please read.") == "Important notice: Please read."

def test_clean_for_speech_italics_and_triple():
    tts = TextToSpeech(VoiceConfig(enabled=False))
    assert tts._clean_for_speech("This is *italic* and _italic2_.") == "This is italic and italic2."
    assert tts._clean_for_speech("This is ***super bold*** text.") == "This is super bold text."

def test_clean_for_speech_lists_and_inline_code():
    tts = TextToSpeech(VoiceConfig(enabled=False))
    text = "Items:\n- **cat**\n- **dog**\n- `fish`"
    cleaned = tts._clean_for_speech(text)
    assert "cat" in cleaned
    assert "dog" in cleaned
    assert "fish" in cleaned
    assert "*" not in cleaned
    assert "`" not in cleaned

def test_clean_for_speech_code_blocks_and_links():
    tts = TextToSpeech(VoiceConfig(enabled=False))
    text = "Check this out:\n```python\nprint('hello')\n```\nVisit [OpenAI](https://openai.com) for details."
    cleaned = tts._clean_for_speech(text)
    assert "Code snippet omitted." in cleaned
    assert "Visit OpenAI for details." in cleaned
    assert "http" not in cleaned

def test_clean_for_speech_headings_and_quotes():
    tts = TextToSpeech(VoiceConfig(enabled=False))
    text = "# Main Title\n## Section 1\n> This is an important **quote** from the author."
    cleaned = tts._clean_for_speech(text)
    assert cleaned == "Main Title Section 1 This is an important quote from the author."

def test_clean_for_speech_empty_and_special():
    tts = TextToSpeech(VoiceConfig(enabled=False))
    assert tts._clean_for_speech("") == ""
    assert tts._clean_for_speech("   ") == ""
    assert tts._clean_for_speech("Normal sentence without formatting.") == "Normal sentence without formatting."
