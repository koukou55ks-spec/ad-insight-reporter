import json
import logging

from openai import OpenAI

from app.settings import settings

logger = logging.getLogger(__name__)


def generate_ai_report(
    summary: list[dict],
    alerts: list[dict],
) -> str | None:
    api_key = settings.openai_api_key

    if not api_key:
        return None

    model = settings.openai_model

    input_data = {
        "summary": summary,
        "alerts": alerts,
    }

    prompt = f"""

    あなたは広告運用アシスタントです

    以下はPythonで計算済みの広告分析結果です
    数値を再計算したり、存在しない事実を追加したりせずに、
    担当者が次に確認すべきことをわかりやすくまとめてください。

    出力形式：
    1. 本日の要約
    2. 重要な変化
    3. 原因候補
    4. 推奨アクション

    異常がない場合は、問題がないことと継続して確認すべき指標を書いてください。

    分析結果
    {json.dumps(input_data, ensure_ascii=False, indent=2)}
    """

    try:
        client = OpenAI(api_key=api_key, timeout=30.0, max_retries=2)

        response = client.responses.create(
            model=model,
            input=prompt,
        )

        return response.output_text

    except Exception:
        logger.exception("AI report generation failed for model %s", model)
        return None
