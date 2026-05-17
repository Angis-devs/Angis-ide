from angis.interpreter import _run_ai_action


def test_ai_keywords():
    result = _run_ai_action("keywords", {"text": "The quick brown fox jumps over the lazy dog near the river bank"})
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(item, tuple) and len(item) == 2 for item in result)
    # Stop words should be filtered out
    words = [w for w, _ in result]
    assert "the" not in words


def test_ai_sentiment_positive():
    result = _run_ai_action("sentiment", {"text": "This is wonderful and amazing and excellent"})
    assert isinstance(result, dict)
    assert result["label"] == "positive"
    assert result["score"] > 0


def test_ai_sentiment_negative():
    result = _run_ai_action("sentiment", {"text": "This is terrible and awful and horrible"})
    assert isinstance(result, dict)
    assert result["label"] == "negative"
    assert result["score"] < 0


def test_ai_sentiment_neutral():
    result = _run_ai_action("sentiment", {"text": "This is a book on the table"})
    assert isinstance(result, dict)
    assert result["label"] == "neutral"


def test_ai_similarity():
    result = _run_ai_action("similar", {"text1": "The quick brown fox", "text2": "The quick brown fox"})
    assert isinstance(result, dict)
    assert result["jaccard"] == 1.0
    assert result["cosine"] == 1.0


def test_ai_similarity_different():
    result = _run_ai_action("similar", {"text1": "The quick brown fox", "text2": "A slow red cat"})
    assert isinstance(result, dict)
    assert result["jaccard"] < 0.5


def test_ai_summarize():
    result = _run_ai_action("summarize", {"text": "Python is a programming language. It is very popular. Many people use it for web development. It is also used for data science. The language is easy to learn. It has a large ecosystem of libraries.", "sentences": 2})
    assert isinstance(result, str)
    assert len(result) > 0


def test_ai_count_words():
    result = _run_ai_action("count_words", {"text": "The quick brown fox jumps"})
    assert result == 5


def test_ai_count_sentences():
    result = _run_ai_action("count_sentences", {"text": "Hello world. How are you? I am fine."})
    assert result == 3


def test_ai_detect_language_english():
    result = _run_ai_action("detect_language", {"text": "The quick brown fox jumps over the lazy dog"})
    assert isinstance(result, dict)
    assert result["language"] == "english"


def test_ai_detect_language_spanish():
    result = _run_ai_action("detect_language", {"text": "El gato esta en la casa con el perro"})
    assert isinstance(result, dict)
    assert result["language"] == "spanish"


def test_ai_classify():
    result = _run_ai_action("classify", {"text": "I love programming in Python", "categories": {"tech": ["python", "programming", "code", "software"], "sports": ["football", "soccer", "basketball"]}})
    assert isinstance(result, dict)
    assert result["category"] == "tech"


def test_ai_generate():
    result = _run_ai_action("generate", {"text": "the cat sat on the mat the cat sat on the chair the cat sat on the floor", "words": 6})
    assert isinstance(result, str)
    assert len(result) > 0


def test_ai_entity():
    result = _run_ai_action("entity", {"text": "Contact me at user@example.com or visit https://angis.ai #AI @angis_dev"})
    assert isinstance(result, dict)
    assert "user@example.com" in result["emails"]
    assert "https://angis.ai" in result["urls"]
    assert "#AI" in result["hashtags"]
    assert "@angis_dev" in result["mentions"]


def test_ai_suggest():
    result = _run_ai_action("suggest", {"text": "programming python package pandas performance", "prefix": "p"})
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(w.startswith("p") for w in result)


def test_ai_readability():
    result = _run_ai_action("readability", {"text": "The cat sat on the mat. The dog ran in the park. The sun is bright today."})
    assert isinstance(result, dict)
    assert "score" in result
    assert "label" in result


def test_ai_ask():
    result = _run_ai_action("ask", {"question": "hello there"})
    assert isinstance(result, str)
    assert len(result) > 0


def test_ai_ask_help():
    result = _run_ai_action("chat", {"text": "what can you do"})
    assert isinstance(result, str)
    assert len(result) > 0


def test_ai_unknown_action():
    import pytest
    from angis.interpreter import AngisRuntimeError
    with pytest.raises(AngisRuntimeError):
        _run_ai_action("nonexistent_action", {"text": "hello"})



