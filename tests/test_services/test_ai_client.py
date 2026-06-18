from app.services.ai_client import mock_contract_analysis


def test_mock_detects_known_keywords():
    text = "This agreement includes a termination clause and confidentiality terms."
    result = mock_contract_analysis(text)
    clause_types = [c.clause_type.lower() for c in result.key_clauses]
    assert "termination" in clause_types
    assert "confidentiality" in clause_types


def test_mock_adds_risk_for_missing_governing_law():
    text = "Payment is due on the first of each month."
    result = mock_contract_analysis(text)
    risk_names = [r.risk for r in result.risks]
    assert any("governing law" in r.lower() for r in risk_names)


def test_mock_risk_score_is_capped():
    text = "No relevant clauses here."
    result = mock_contract_analysis(text)
    assert 0 <= result.risk_score <= 100


def test_no_groq_key_returns_mock_with_error():
    from app.services.ai_client import ai_contract_analysis
    result = ai_contract_analysis("Some contract text.", groq_api_key="")
    assert result.ai_error == "NO GROQ_API_KEY FOUND"
