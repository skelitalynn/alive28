export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export async function getDailyPrompt(dayIndex: number) {
  const res = await fetch(`${API_BASE}/dailyPrompt?dayIndex=${dayIndex}`);
  if (!res.ok) throw new Error("dailyPrompt failed");
  return res.json();
}

export async function checkin(payload: any) {
  const res = await fetch(`${API_BASE}/checkin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("checkin failed");
  return res.json();
}

export async function confirmTx(payload: any) {
  const res = await fetch(`${API_BASE}/tx/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("tx confirm failed");
  return res.json();
}

export async function confirmSbt(payload: any) {
  const res = await fetch(`${API_BASE}/sbt/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("sbt confirm failed");
  return res.json();
}

export async function getProgress(address: string) {
  const res = await fetch(`${API_BASE}/progress?address=${address}`);
  if (!res.ok) throw new Error("progress failed");
  return res.json();
}

export async function getReport(address: string, range: "week" | "final") {
  const res = await fetch(`${API_BASE}/report?address=${address}&range=${range}`);
  if (!res.ok) throw new Error("report failed");
  return res.json();
}
