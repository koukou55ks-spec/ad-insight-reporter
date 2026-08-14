import json
import os

from pathlib import Path
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv(
    Path(__file__).resolve().parents[1] / ".env"
)


def generate_ai_report(
    summary: list[dict],
    alerts: list[dict],
) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None
    
    model = os.getenv("OPENAI_MODEL")

    input_data = {
        "summary": summary,
        "alerts": alerts,
    }

    prompt = f"""

    あなたは広告運用アシスタントです

    以下はPythonで計算済みの広告分析結果です。
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
        client = OpenAI(api_key=api_key)    

        response = client.responses.create(
            model=model,
            input=prompt,
        )

        return response.output_text
    
    except Exception:
        return None
