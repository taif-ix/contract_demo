import json

from app.schemas import AnalysisResult, ClauseItem, RiskItem
from app.utils.text import find_best_paragraph

_CONTRACT_KEYWORDS = [
    "termination", "confidentiality", "payment", "governing law",
    "liability", "indemnity", "security", "arbitration",
]


def mock_contract_analysis(text: str) -> AnalysisResult:
    """Rule-based fallback — no external API required."""
    lower = text.lower()

    clauses = [
        ClauseItem(
            clause_type=kw.title(),
            clause_text=find_best_paragraph(text, kw),
        )
        for kw in _CONTRACT_KEYWORDS
        if kw in lower
    ]

    risks: list[RiskItem] = []
    if "termination" not in lower:
        risks.append(RiskItem(
            risk="Termination clause may be missing",
            severity="high",
            reason="No termination keyword found.",
        ))
    if "governing law" not in lower:
        risks.append(RiskItem(
            risk="Governing law clause may be missing",
            severity="medium",
            reason="No governing law keyword found.",
        ))

    return AnalysisResult(
        document_type="contract",
        key_clauses=clauses,
        risks=risks,
        risk_score=max(0, 100 - len(risks) * 20),
        mode="mock_analysis",
    )


def ai_contract_analysis(text: str, groq_api_key: str) -> AnalysisResult:
    """Groq LLM analysis; falls back to mock on any error."""
    if not groq_api_key:
        result = mock_contract_analysis(text)
        result.ai_error = "NO GROQ_API_KEY FOUND"
        return result

    try:
        from groq import Groq  # imported lazily — optional dependency

        prompt = f"""
You are a contract review assistant.
Analyze the contract text and return ONLY valid JSON. Do not include markdown or explanation.

Use this schema exactly:
{{
  "document_type": "contract",
  "parties": [],
  "effective_date": "",
  "expiry_date": "",
  "contract_value": "",
  "governing_law": "",
  "key_clauses": [{{"clause_type": "", "clause_text": ""}}],
  "risks": [{{"risk": "", "severity": "low|medium|high", "reason": ""}}],
  "risk_score": 0
}}

risk_score must be 0–100. 100 = safest. 0 = highest risk.

Contract text:
{text[:12000]}
"""
        client = Groq(api_key=groq_api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = (
            response.choices[0].message.content
            .strip()
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )
        data = json.loads(raw)
        data["mode"] = "groq_analysis"

        return AnalysisResult(
            document_type=data.get("document_type", ""),
            parties=data.get("parties", []),
            effective_date=data.get("effective_date", ""),
            expiry_date=data.get("expiry_date", ""),
            contract_value=data.get("contract_value", ""),
            governing_law=data.get("governing_law", ""),
            key_clauses=[ClauseItem(**c) for c in data.get("key_clauses", [])],
            risks=[RiskItem(**r) for r in data.get("risks", [])],
            risk_score=int(data.get("risk_score", 0)),
            mode="groq_analysis",
        )

    except Exception as exc:
        result = mock_contract_analysis(text)
        result.ai_error = repr(exc)
        return result
