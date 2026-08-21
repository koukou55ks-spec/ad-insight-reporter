import logging

from app import ai_report


def test_generate_ai_report_logs_client_failures(monkeypatch, caplog):
    def fail_to_create_client(*args, **kwargs):
        raise RuntimeError("service unavailable")

    monkeypatch.setattr(ai_report.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(ai_report, "OpenAI", fail_to_create_client)

    with caplog.at_level(logging.ERROR):
        result = ai_report.generate_ai_report([], [])

    assert result is None
    assert "AI report generation failed" in caplog.text
