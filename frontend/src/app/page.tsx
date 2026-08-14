"use client";

import { ChangeEvent, FormEvent, useState } from "react";

type SummaryRow = {
  campaign: string;
  impressions: number;
  clicks: number;
  cost: number;
  conversions: number;
  revenue: number;
  ctr: number | null;
  cpa: number | null;
  roas: number | null;
};

type Alert = {
  campaign: string;
  type: string;
  message: string;
  previous_value: string;
  current_value: string;
  unit: string;
};

type AnalysisResponse = {
  status: string;
  analysis_id?: number;
  file_name?: string;
  row_count?: number;
  summary?: SummaryRow[];
  alerts?: Alert[];
  ai_report?: string | null;
  message?: string;
  validation_errors?: string[];
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    setFile(event.target.files?.[0] ?? null);
    setResult(null);
    setMessage("");
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!file) {
      setMessage("CSVファイルを選択してください。");
      return;
    }

    const formData = new FormData();
    formData.append("csv_file", file);

    setLoading(true);
    setMessage("");
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/api/imports`,
        {
          method: "POST",
          body: formData,
        },
      );

      const data: AnalysisResponse =
        await response.json();

      if (!response.ok || data.status === "error") {
        const errors =
          data.validation_errors?.join("\n") ?? "";

        setMessage(
          [data.message, errors]
            .filter(Boolean)
            .join("\n"),
        );
        return;
      }

      setResult(data);
    } catch {
      setMessage(
        "FastAPIに接続できません。バックエンドを起動してください。",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <header>
        <p className="eyebrow">
          AD INSIGHT REPORTER
        </p>

        <h1>広告成果を、すぐに判断できる状態へ。</h1>

        <p className="description">
          CSVをアップロードすると、キャンペーン別の成果と
          異常を自動分析します。
        </p>
      </header>

      <section className="upload-card">
        <h2>広告データを分析</h2>

        <form onSubmit={handleSubmit}>
          <label htmlFor="csv-file">
            広告CSV
          </label>

          <input
            id="csv-file"
            type="file"
            accept=".csv,text/csv"
            onChange={handleFileChange}
          />

          <button
            type="submit"
            disabled={loading}
          >
            {loading ? "分析中..." : "分析を開始"}
          </button>
        </form>

        {file && (
          <p className="selected-file">
            選択中：{file.name}
          </p>
        )}

        {message && (
          <p className="error-message">
            {message}
          </p>
        )}
      </section>

      {result && (
        <section className="results">
          <div className="result-header">
            <div>
              <p className="eyebrow">ANALYSIS RESULT</p>
              <h2>分析結果</h2>
            </div>

            <p>
              {result.file_name} / {result.row_count}行
            </p>
          </div>

          <section className="alert-section">
            <h3>異常検知</h3>

            {result.alerts &&
            result.alerts.length > 0 ? (
              <div className="alert-list">
                {result.alerts.map((alert, index) => (
                  <article
                    className="alert-card"
                    key={`${alert.campaign}-${alert.type}-${index}`}
                  >
                    <p className="alert-title">
                      {alert.campaign}（{alert.type}）
                    </p>

                    <p>{alert.message}</p>

                    <small>
                      前週：{alert.previous_value}
                      {alert.unit}
                      {" / "}
                      今週：{alert.current_value}
                      {alert.unit}
                    </small>
                  </article>
                ))}
              </div>
            ) : (
              <p className="empty-message">
                検出された異常はありません。
              </p>
            )}
          </section>

          <section className="table-section">
            <h3>キャンペーン別集計</h3>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>キャンペーン</th>
                    <th>広告費</th>
                    <th>CV</th>
                    <th>CTR</th>
                    <th>CPA</th>
                    <th>ROAS</th>
                  </tr>
                </thead>

                <tbody>
                  {result.summary?.map((row) => (
                    <tr key={row.campaign}>
                      <td>{row.campaign}</td>
                      <td>
                        {row.cost.toLocaleString()}円
                      </td>
                      <td>{row.conversions}</td>
                      <td>
                        {row.ctr === null
                          ? "—"
                          : `${row.ctr}%`}
                      </td>
                      <td>
                        {row.cpa === null
                          ? "—"
                          : `${row.cpa.toLocaleString()}円`}
                      </td>
                      <td>
                        {row.roas === null
                          ? "—"
                          : `${row.roas}%`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {result.ai_report && (
            <section className="report-section">
              <h3>AI日報</h3>
              <pre className="ai-report">{result.ai_report}</pre>
            </section>
          )}
        </section>
      )}
    </main>
  );
}
