export type SummaryRow = {
  campaign: string;
  cost: number;
  conversions: number;
  ctr: number | null;
  cpa: number | null;
  roas: number | null;
};

export type AlertRow = {
  campaign: string;
  type: string;
  message: string;
  previous_value: string;
  current_value: string;
  unit: string;
};

export type ImportSuccessResponse = {
  status: "success";
  analysis_id: number;
  file_name: string;
  row_count: number;
  summary: SummaryRow[];
  alerts: AlertRow[];
  ai_report: string | null;
};

type ImportErrorResponse = {
  status: "error";
  message: string;
  validation_errors?: string[] | null;
};

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
