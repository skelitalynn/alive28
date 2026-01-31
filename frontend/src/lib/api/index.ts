import { httpClient } from "./httpClient";
import { mockClient } from "./mockClient";

const mode = process.env.NEXT_PUBLIC_API_MODE || "mock";

export const api = mode === "http" ? httpClient : mockClient;

export type { ApiClient, CheckinResult, DailySnapshot, HomeSnapshot, ProgressData, ReportData } from "./client";
