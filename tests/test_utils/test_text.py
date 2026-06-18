from app.utils.text import find_best_paragraph, split_into_paragraphs


def test_split_into_paragraphs_basic():
    text = "First paragraph about payment.\n\nSecond paragraph about termination."
    chunks = split_into_paragraphs(text)
    assert len(chunks) == 2
    assert "payment" in chunks[0]


def test_split_filters_short_chunks():
    text = "Hi\n\nThis is a longer paragraph with enough content to pass the filter."
    chunks = split_into_paragraphs(text)
    assert all(len(c) > 20 for c in chunks)


def test_find_best_paragraph_returns_match():
    text = "Payment is due on the first of each month.\n\nTermination requires 30 days notice."
    result = find_best_paragraph(text, "termination")
    assert "30 days" in result


def test_find_best_paragraph_returns_empty_when_no_match():
    text = "This contract has no relevant clauses."
    result = find_best_paragraph(text, "arbitration")
    assert result == ""
