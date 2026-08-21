"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { uploadCsv } from "@/lib/api";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [selectionError, setSelectionError] = useState("");
  const analysis = useMutation({
    mutationKey: ["imports"],
    mutationFn: uploadCsv,
  });

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
    setSelectionError("");
    analysis.reset();
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!file) {
      setSelectionError("CSVファイルを選択してください。");
      return;
    }

    setSelectionError("");
    analysis.reset();
    analysis.mutate(file);
  }

  const message = selectionError || analysis.error?.message || "";
  const result = analysis.data;

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-4 py-12 text-slate-900 sm:px-6 lg:py-16">
      <header className="space-y-4">
        <p className="text-xs font-bold tracking-[0.16em] text-blue-600">AD INSIGHT REPORTER</p>
        <h1 className="max-w-3xl text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
          広告成果を、すぐに判断できる状態へ。
        </h1>
        <p className="max-w-2xl text-lg text-slate-500">
          CSVをアップロードすると、キャンペーン別の成果と異常を自動分析します。
        </p>
      </header>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>広告データを分析</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4" onSubmit={handleSubmit}>
            <label className="text-sm font-medium text-slate-700" htmlFor="csv-file">広告CSV</label>
            <input
              id="csv-file"
              className="h-11 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm file:mr-4 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1 file:text-sm file:font-medium"
              type="file"
              accept=".csv,text/csv"
              onChange={handleFileChange}
            />
            <Button className="w-fit" type="submit" disabled={analysis.isPending}>
              {analysis.isPending ? "分析中..." : "分析を開始"}
            </Button>
          </form>

          {file && <p className="mt-4 text-sm text-slate-500">選択中：{file.name}</p>}
          {message && (
            <Alert className="mt-4 border-red-200 bg-red-50 text-red-950">
              <AlertTitle>分析に失敗しました</AlertTitle>
              <AlertDescription className="whitespace-pre-line">{message}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {result && (
        <Card className="mt-8">
          <CardHeader className="flex-row items-end justify-between border-b border-slate-200">
            <div>
              <p className="text-xs font-bold tracking-[0.16em] text-blue-600">ANALYSIS RESULT</p>
              <CardTitle className="mt-2">分析結果</CardTitle>
            </div>
            <p className="text-sm text-slate-500">{result.file_name} / {result.row_count}行</p>
          </CardHeader>
          <CardContent className="space-y-8 pt-6">
            <section>
              <h3 className="mb-4 text-xl font-semibold">異常検知</h3>
              {result.alerts.length > 0 ? (
                <div className="grid gap-3">
                  {result.alerts.map((alert, index) => (
                    <Alert key={`${alert.campaign}-${alert.type}-${index}`}>
                      <AlertTitle>{alert.campaign}（{alert.type}）</AlertTitle>
                      <AlertDescription>
                        <p>{alert.message}</p>
                        <p className="mt-2 text-xs text-amber-800">
                          前週：{alert.previous_value}{alert.unit} / 今週：{alert.current_value}{alert.unit}
                        </p>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500">検出された異常はありません。</p>
              )}
            </section>

            <section>
              <h3 className="mb-4 text-xl font-semibold">キャンペーン別集計</h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>キャンペーン</TableHead>
                    <TableHead>広告費</TableHead>
                    <TableHead>CV</TableHead>
                    <TableHead>CTR</TableHead>
                    <TableHead>CPA</TableHead>
                    <TableHead>ROAS</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {result.summary.map((row) => (
                    <TableRow key={row.campaign}>
                      <TableCell className="font-medium">{row.campaign}</TableCell>
                      <TableCell>{row.cost.toLocaleString()}円</TableCell>
                      <TableCell>{row.conversions}</TableCell>
                      <TableCell>{row.ctr === null ? "—" : `${row.ctr}%`}</TableCell>
                      <TableCell>{row.cpa === null ? "—" : `${row.cpa.toLocaleString()}円`}</TableCell>
                      <TableCell>{row.roas === null ? "—" : `${row.roas}%`}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </section>

            {result.ai_report && (
              <section>
                <h3 className="mb-4 text-xl font-semibold">AI日報</h3>
                <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-5 font-sans text-sm leading-7 text-slate-700">
                  {result.ai_report}
                </pre>
              </section>
            )}
          </CardContent>
        </Card>
      )}
    </main>
  );
}
