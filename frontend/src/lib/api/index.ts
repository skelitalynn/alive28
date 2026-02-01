import { httpClient } from "./httpClient";

// Force HTTP mode so frontend always uses backend (DEMO_MODE is handled server-side).
export const api = httpClient;

export type { ApiClient, CheckinResult, DailySnapshot, HomeSnapshot, ProgressData, ReportData } from "./client";
