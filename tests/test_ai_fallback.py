from angis.intents import match_intent
from angis.ai import teach_phrase
from angis.ir import AppStart, Reference
import pytest

def test_ai_fallback_translation():
    # Teach a new phrase
    teach_phrase("create a window named myapp", "app myapp")
    
    # Test if match_intent uses the AI fallback
    result = match_intent("create a window named myapp")
    assert isinstance(result, AppStart)
    assert result.title == Reference(name="myapp")

def test_italian_fallback():
    # "mostra" is Italian for "say/show"
    result = match_intent('mostra "ciao"')
    assert result.value == "ciao"

def test_set_heuristic_fallback():
    # "score = 10" is not standard Angis (it usually wants "set score to 10")
    result = match_intent("score = 10")
    assert result.name == "score"
    assert result.value == 10
