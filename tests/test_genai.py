import io
import json
import urllib.error
import pytest
from portfolio import genai
from portfolio.ai_web import create_app


def test_document_answer_includes_traceable_evidence():
    result = genai.answer("How long are backups retained?")
    assert not result["abstained"]
    assert "30 days" in result["answer"]
    assert result["citations"]
    assert result["mode"] == "offline"


def test_unknown_question_abstains():
    result = genai.answer("quasar mitochondria photosynthesis")
    assert result["abstained"]
    assert result["sources"] == []


def test_support_drafts_never_execute_actions():
    result = genai.support("I need a refund")
    assert result["needs_human"]
    assert "14 days" in result["draft"]
    assert result["citations"]


def test_meeting_parser_does_not_convert_suggestions_to_actions():
    text = "Mira: Maybe build mobile someday.\nACTION: Dev | Write tests | Friday"
    result = genai.meeting(text)
    assert len(result["actions"]) == 1
    assert result["actions"][0]["owner"] == "Dev"
    assert result["actions"][0]["evidence"] in text


def test_empty_transcript_rejected():
    with pytest.raises(ValueError):
        genai.meeting(" ")


def test_missing_credentials_produces_actionable_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(genai.ProviderError, match="OPENAI_API_KEY"):
        genai.answer("backups", "openai")


def test_fabricated_citations_are_rejected(monkeypatch):
    monkeypatch.setattr(genai, "generate", lambda *args: dict(answer="Fake", citations=["fake.md"], abstained=False))
    with pytest.raises(genai.ProviderError, match="outside"):
        genai.answer("backups", "openai")


def test_fabricated_meeting_evidence_is_rejected(monkeypatch):
    monkeypatch.setattr(genai, "generate", lambda *args: dict(summary="x", actions=[
        dict(owner="Dev", task="Pay bill", due="Friday", evidence="Invented commitment")]))
    with pytest.raises(genai.ProviderError, match="verbatim"):
        genai.meeting("Dev: Let's talk later", "openai")


def test_api_contract_validates_json_and_uses_no_storage(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder-not-a-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    def transport(request, timeout):
        payload = json.loads(request.data)
        assert payload["store"] is False
        assert payload["text"]["format"]["strict"] is True
        assert timeout == 45
        return io.BytesIO(json.dumps({"status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps(dict(answer="ok", citations=[], abstained=True))}]}]}).encode())
    assert genai.generate("Answer", {}, genai.ANSWER, transport)["abstained"]


@pytest.mark.parametrize("status,parts", [
    ("incomplete", []), ("completed", [{"type": "refusal", "refusal": "No"}]),
    ("completed", [{"type": "output_text", "text": '{"answer": 3}'}]),
])
def test_api_rejects_incomplete_refused_or_invalid_results(monkeypatch, status, parts):
    monkeypatch.setenv("OPENAI_API_KEY", "placeholder")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    def transport(*args, **kwargs):
        return io.BytesIO(json.dumps({"status": status, "output": [{"type": "message", "content": parts}]}).encode())
    with pytest.raises(genai.ProviderError):
        genai.generate("Answer", {}, genai.ANSWER, transport)


@pytest.mark.parametrize("project", list(__import__('portfolio.ai_web', fromlist=['PROJECTS']).PROJECTS))
def test_ai_browser_flow_csrf_and_consent(project):
    client = create_app(project, {"TESTING": True}).test_client()
    assert client.get("/").status_code == 200
    assert client.post("/", data={"text": "backups"}).status_code == 400
    with client.session_transaction() as session:
        csrf = session["csrf"]
    response = client.post("/", data=dict(csrf=csrf, text="ACTION: Dev | Write tests | Friday", mode="offline"))
    assert response.status_code == 200
    assert b"offline mode" in response.data
    response = client.post("/", data=dict(csrf=csrf, text="backups", mode="openai"))
    assert b"Confirm sending" in response.data
