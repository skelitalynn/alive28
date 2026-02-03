import type { Store, User, DailyLog } from "./schema";

export const LS_KEY = "alive28:v1";
export const CHALLENGE_ID = 1;
export const STORE_EVENT = "alive28:store";

const emptyStore = (): Store => ({ users: {}, logs: [] });

function getStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function emitStoreEvent() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(STORE_EVENT));
}

export function loadStore(): Store {
  const storage = getStorage();
  if (!storage) return emptyStore();
  try {
    const raw = storage.getItem(LS_KEY);
    if (!raw) return emptyStore();
    const data = JSON.parse(raw) as Store;
    if (!data.users) data.users = {};
    for (const key of Object.keys(data.users)) {
      const user = data.users[key];
      if (!user.milestones || typeof user.milestones !== "object") {
        user.milestones = {};
      }
    }
    if (!Array.isArray(data.logs)) data.logs = [];
    return data;
  } catch {
    return emptyStore();
  }
}

export function saveStore(store: Store) {
  const storage = getStorage();
  if (!storage) return;
  storage.setItem(LS_KEY, JSON.stringify(store));
  emitStoreEvent();
}

export function resetStore() {
  const storage = getStorage();
  if (!storage) return;
  storage.removeItem(LS_KEY);
  emitStoreEvent();
}

export function todayDateKey(timezone = Intl.DateTimeFormat().resolvedOptions().timeZone) {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export function normalizeText(s: string) {
  return (s || "").trim().replace(/\s+/g, " ").slice(0, 280);
}

function getRandomValues(bytes: Uint8Array) {
  if (typeof crypto !== "undefined" && crypto.getRandomValues) {
    crypto.getRandomValues(bytes);
    return;
  }
  for (let i = 0; i < bytes.length; i += 1) {
    bytes[i] = Math.floor(Math.random() * 256);
  }
}

export function uuid() {
  const a = new Uint8Array(16);
  getRandomValues(a);
  a[6] = (a[6] & 0x0f) | 0x40;
  a[8] = (a[8] & 0x3f) | 0x80;
  const hex = [...a].map((b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function getUser(store: Store, address: string): User {
  const key = address.toLowerCase();
  if (!store.users[key]) {
    store.users[key] = {
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
      startDateKey: null,
      streak: 0,
      lastDateKey: null,
      dayMintCount: 0,
      finalMinted: false,
      finalNftTxHash: null,
      milestones: {}
    };
    saveStore(store);
  }
  return store.users[key];
}

export function findLog(store: Store, address: string, dateKey: string): DailyLog | null {
  const a = address.toLowerCase();
  return (
    store.logs.find((l) => l.address === a && l.challengeId === CHALLENGE_ID && l.dateKey === dateKey) || null
  );
}

export function computeDayIndex(user: User, dateKey: string) {
  if (!user.startDateKey) {
    user.startDateKey = dateKey;
    return 1;
  }
  const [sy, sm, sd] = user.startDateKey.split("-").map(Number);
  const [ty, tm, td] = dateKey.split("-").map(Number);
  const s = new Date(sy, sm - 1, sd);
  const t = new Date(ty, tm - 1, td);
  const diff = Math.round((t.getTime() - s.getTime()) / (24 * 3600 * 1000));
  return diff + 1;
}

export function peekDayIndex(user: User, dateKey: string) {
  if (!user.startDateKey) return 1;
  const [sy, sm, sd] = user.startDateKey.split("-").map(Number);
  const [ty, tm, td] = dateKey.split("-").map(Number);
  const s = new Date(sy, sm - 1, sd);
  const t = new Date(ty, tm - 1, td);
  const diff = Math.round((t.getTime() - s.getTime()) / (24 * 3600 * 1000));
  return diff + 1;
}

export function updateStreak(user: User, dateKey: string) {
  if (!user.lastDateKey) {
    user.streak = 1;
    user.lastDateKey = dateKey;
    return;
  }
  if (user.lastDateKey === dateKey) return;

  const [ly, lm, ld] = user.lastDateKey.split("-").map(Number);
  const last = new Date(ly, lm - 1, ld);
  const next = new Date(last);
  next.setDate(last.getDate() + 1);
  const nk = `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, "0")}-${String(next.getDate()).padStart(
    2,
    "0"
  )}`;

  if (nk === dateKey) user.streak += 1;
  else user.streak = 1;

  user.lastDateKey = dateKey;
}
