from decimal import Decimal
from io import BytesIO
from typing import Annotated, Literal

import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from app.ai_report import generate_ai_report
from app.analysis import (
    detect_anomalies,
    summarize_data,
    validate_dataframe,
)
from app.database import get_connection
from app.logging_config import get_logger

logger = get_logger(__name__)


class CSVInputError(Exception):
    """入力CSVが分析可能な形式でない場合に発生するエラー。"""

    def __init__(self, message: str, details: list[str] | None = None) -> None:
        self.message = message
        self.details = details or []
        super().__init__(message)


class SummaryRow(BaseModel):
    campaign: str
    impressions: int
    clicks: int
    cost: float
    conversions: int
    revenue: float
    ctr: float | None
    cpa: float | None
    roas: float | None


class AlertRow(BaseModel):
    campaign: str
    type: str
    message: str
    previous_value: str
    current_value: str
    unit: str


class ImportSuccessResponse(BaseModel):
    status: Literal["success"]
    analysis_id: int
    file_name: str
    row_count: int
    summary: list[SummaryRow]
    alerts: list[AlertRow]
    ai_report: str | None = None


class ImportErrorResponse(BaseModel):
    status: Literal["error"]
    message: str
    validation_errors: list[str] | None = None


ImportResponse = ImportSuccessResponse | ImportErrorResponse


app = FastAPI(
    title="Ad Insight Reporter",
    description="広告データを分析し、異常検知と日報生成を行うシステム",
    version="1.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.68.50",
        "http://192.168.68.50:3000",
        "https://ad-insight-reporter.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_COLUMNS = {
    "date",
    "campaign",
    "impressions",
    "clicks",
    "cost",
    "conversions",
    "revenue",
}

COUNT_COLUMNS = [
    "impressions",
    "clicks",
    "conversions",
]


def parse_csv(file_content: bytes) -> pd.DataFrame:
    """CSVを読み込み、必須列とデータ形式を検証する。"""
    try:
        df = pd.read_csv(BytesIO(file_content))
    except pd.errors.EmptyDataError as exc:
        raise CSVInputError("CSVファイルにデータがありません") from exc
    except pd.errors.ParserError as exc:
        raise CSVInputError("CSVの形式を読み込めませんでした") from exc
    except UnicodeDecodeError as exc:
        raise CSVInputError("文字コードを読み取れませんでした") from exc

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise CSVInputError("必要な列がありません:" + ",".join(sorted(missing_columns)))

    validation_errors = validate_dataframe(df)
    if validation_errors:
        raise CSVInputError("CSVの内容に問題があります", validation_errors)

    return df


def build_analysis(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict], str | None]:
    """集計・異常検知・AIレポートを共通して実行する。"""
    summary = summarize_data(df)
    alerts = detect_anomalies(df)
    ai_report = generate_ai_report(summary.to_dict(orient="records"), alerts)
    return summary, alerts, ai_report


def persist_import(connection, df: pd.DataFrame, file_name: str) -> int:
    """インポート履歴と明細を同一トランザクションで保存する。"""
    result = connection.execute(
        text(
            """
            INSERT INTO import_jobs (
                file_name, status, imported_rows, error_count
            )
            VALUES (
                :file_name, :status, :imported_rows, :error_count
            )
            RETURNING id
            """
        ),
        {
            "file_name": file_name,
            "status": "success",
            "imported_rows": len(df),
            "error_count": 0,
        },
    )
    import_job_id = result.scalar_one()
    save_ad_results(connection, df, import_job_id)
    return import_job_id


def save_import(df: pd.DataFrame, file_name: str) -> int:
    """DB接続・commit・rollback・closeを一箇所で管理する。"""
    connection = get_connection()
    try:
        import_job_id = persist_import(connection, df, file_name)
        connection.commit()
        return import_job_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def save_ad_results(
    connection,
    df: pd.DataFrame,
    import_job_id: int,
) -> None:
    data = df.copy()

    data["date"] = pd.to_datetime(data["date"]).dt.date

    for column in COUNT_COLUMNS:
        data[column] = pd.to_numeric(data[column]).astype(int)

    records = [
        {
            "import_job_id": import_job_id,
            "result_date": row["date"],
            "campaign": row["campaign"],
            "impressions": int(row["impressions"]),
            "clicks": int(row["clicks"]),
            "cost": Decimal(str(row["cost"])),
            "conversions": int(row["conversions"]),
            "revenue": Decimal(str(row["revenue"])),
        }
        for _, row in data.iterrows()
    ]

    connection.execute(
        text(
            """
        INSERT INTO ad_results(
        import_job_id,
        result_date,
        campaign,
        impressions,
        clicks,
        cost,
        conversions,
        revenue
        )
        VALUES (
            :import_job_id,
            :result_date,
            :campaign,
            :impressions,
            :clicks,
            :cost,
            :conversions,
            :revenue
        )
        """
        ),
        records,
    )


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "ad-insight-reporter", "status": "ok"}


@app.post("/api/imports")
async def import_csv_api(
    csv_file: Annotated[UploadFile, File()],
) -> ImportResponse:
    file_name = csv_file.filename or "unknown.csv"
    file_content = await csv_file.read()
    logger.info(
        "CSV import started",
        file_name=file_name,
        content_length=len(file_content),
    )

    try:
        df = parse_csv(file_content)
    except CSVInputError as exc:
        logger.warning(
            "CSV import rejected",
            file_name=file_name,
            reason=exc.message,
        )
        return ImportErrorResponse(
            status="error",
            message=exc.message,
            validation_errors=exc.details or None,
        )

    # pandas, the database driver, and the OpenAI client are synchronous. Run
    # them outside the event loop so concurrent requests remain responsive.
    summary, alerts, ai_report = await run_in_threadpool(build_analysis, df)
    import_job_id = await run_in_threadpool(save_import, df, file_name)
    logger.info(
        "CSV import completed",
        file_name=file_name,
        row_count=len(df),
        analysis_id=import_job_id,
        alert_count=len(alerts),
        ai_report_generated=ai_report is not None,
    )
    return ImportSuccessResponse(
        status="success",
        analysis_id=import_job_id,
        file_name=file_name,
        row_count=len(df),
        summary=summary.to_dict(orient="records"),
        alerts=alerts,
        ai_report=ai_report,
    )


@app.get("/health")
def health_check() -> JSONResponse:
    """アプリとDBの両方が利用可能か確認する。"""
    connection = None
    try:
        connection = get_connection()
        connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Database health check failed", error=str(exc))
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable"},
        )
    finally:
        if connection is not None:
            connection.close()

    return JSONResponse(content={"status": "ok", "database": "ok"})
