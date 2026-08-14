from app.database import get_connection, initialize_database
from app.analysis import (
    detect_anomalies,
    summarize_data,
    validate_dataframe,
)
from app.ai_report import generate_ai_report
from io import BytesIO

import pandas as pd
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware




app = FastAPI(
    title="Ad Insight Reporter",
    description="広告データを分析し、異常検知と日報生成を行うシステム",
    version="1.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.68.50",
        "http://192.168.68.50:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app/templates")

initialize_database()

REQUIRED_COLUMNS = {
    "date",
    "campaign",
    "impressions",
    "clicks",
    "cost",
    "conversions",
    "revenue",
}

NUMERIC_COLUMNS = [
    "impressions",
    "clicks",
    "cost",
    "conversions",
    "revenue",
]



def save_ad_results(
    connection,
    df: pd.DataFrame,
    import_job_id: int,
) -> None:
    data = df.copy()

    data["date"] = pd.to_datetime(
        data["date"]
    ).dt.strftime("%Y-%m-%d")

    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(
            data[column]
        ).astype(int)
    
    records = [
        (
            import_job_id,
            row["date"],
            row["campaign"],
            row["impressions"],
            row["clicks"],
            row["cost"],
            row["conversions"],
            row["revenue"],
        )
        for _, row in data.iterrows()
    ]

    connection.executemany(
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

def render_home(request: Request, **context):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
    )

@app.get("/")
def root(request: Request):
    return render_home(request)



@app.post("/upload")
async def upload_csv(
    request: Request,
    csv_file: UploadFile = File(...),
):
    file_content = await csv_file.read()

    try:
        df = pd.read_csv(BytesIO(file_content))
    except pd.errors.EmptyDataError:
        return render_home(
            request,
            errors="CSVファイルにデータがありません"
        )
    except pd.errors.ParserError:
        return render_home(
            request,
            errors="CSVの形式を読み込めませんでした",
        )
    except UnicodeDecodeError:
        return render_home(
            request,
            error="文字コードを読み取れませんでした",
        )

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        return render_home(
            request,
            error=(
                "必要な列がありません:"
                + ",".join(sorted(missing_columns))
            ),
        )
    validation_errors = validate_dataframe(df)

    if validation_errors:
        return render_home(
            request,
            error="CSVの内容に問題があります",
            validation_errors=validation_errors,
        )
    
    summary = summarize_data(df)
    alerts = detect_anomalies(df)
    ai_report = generate_ai_report(
        summary.to_dict(orient="records"),
        alerts,
    )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO import_jobs (
                file_name,
                status,
                imported_rows,
                error_count
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                csv_file.filename or "unknown.csv",
                "success",
                len(df),
                0,
            ),
        )

        import_job_id = cursor.lastrowid

        save_ad_results(
            connection,
            df,
            import_job_id,
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
    
    return render_home(
        request,
        message="CSVを読み込みました",
        file_name=csv_file.filename,
        row_count=len(df),        
        columns=",".join(df.columns),
        summary=summary.to_dict(orient="records"),
        alerts=alerts,
        import_job_id=import_job_id,
    )

@app.post("/api/imports")
async def import_csv_api(
    csv_file: UploadFile = File(...),
):
    file_content = await csv_file.read()

    try:
        df = pd.read_csv(BytesIO(file_content))
    except pd.errors.EmptyDataError:
        return {
            "status": "error",
            "message": "CSVファイルにデータがありません",
        }
    except pd.errors.ParserError:
        return {
            "status": "error",
            "message": "CSVの形式を読み込めませんでした",
        }
    except UnicodeDecodeError:
        return {
            "status": "error",
            "message": "文字コードを読み取れませんでした",
        }

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        return {
            "status": "error",
            "message": (
                "必要な列がありません:"
                + ",".join(sorted(missing_columns))
            ),
        }

    validation_errors = validate_dataframe(df)

    if validation_errors:
        return {
            "status": "error",
            "message": "CSVの内容に問題があります",
            "validation_errors": validation_errors,
        }

    summary = summarize_data(df)
    alerts = detect_anomalies(df)
    ai_report = generate_ai_report(
        summary.to_dict(orient="records"),
        alerts,
    )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO import_jobs (
                file_name,
                status,
                imported_rows,
                error_count
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                csv_file.filename or "unknown.csv",
                "success",
                len(df),
                0,
            ),
        )

        import_job_id = cursor.lastrowid

        save_ad_results(
            connection,
            df,
            import_job_id,
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return {
        "status": "success",
        "analysis_id": import_job_id,
        "file_name": csv_file.filename,
        "row_count": len(df),
        "summary": summary.to_dict(orient="records"),
        "alerts": alerts,
        "ai_report": ai_report,
    }
        

@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
    }
