import type { components } from "@/lib/api-types";

export type SummaryRow = components["schemas"]["SummaryRow"];
export type AlertRow = components["schemas"]["AlertRow"];
export type ImportSuccessResponse = components["schemas"]["ImportSuccessResponse"];
type ImportErrorResponse = components["schemas"]["ImportErrorResponse"];

type ImportResponse = ImportSuccessResponse | ImportErrorResponse;

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

function getErrorMessage(data: ImportErrorResponse): string {
  return [data.message, data.validation_errors?.join("\n")]
    .filter(Boolean)
    .join("\n");
}

export async function uploadCsv(file: File): Promise<ImportSuccessResponse> {
  const formData = new FormData();
  formData.append("csv_file", file);

  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/imports`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new ApiError("FastAPIに接続できません。バックエンドを起動してください。");
  }

  let data: ImportResponse;
  try {
    data = (await response.json()) as ImportResponse;
  } catch {
    throw new ApiError("バックエンドから不正なレスポンスが返されました。");
  }

  if (!response.ok || data.status === "error") {
    throw new ApiError(
      data.status === "error"
        ? getErrorMessage(data)
        : "広告データの分析に失敗しました。",
    );
  }

  return data;
}
