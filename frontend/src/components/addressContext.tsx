"use client";

import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { MutableRefObject, ReactNode } from "react";
import { randomHex } from "../lib/logic/proof";
import { resetStore, STORE_EVENT } from "../lib/store/localStore";

const LAST_ADDR_KEY = "alive28:last_addr";
const ADDR_SOURCE_KEY = "alive28:addr_source"; // "wallet" | "manual" — 仅 manual 在刷新后恢复

type AddressContextValue = {
  address: string;
  input: string;
  setInput: (value: string) => void;
  setAddress: (addr: string, source?: "wallet" | "manual") => void;
  applyInputAsAddress: () => void;
  randomAddress: () => void;
  resetData: () => void;
  focusInput: () => void;
  inputRef: MutableRefObject<HTMLInputElement | null>;
  storeVersion: number;
  ready: boolean;
};

const AddressContext = createContext<AddressContextValue | null>(null);

export function AddressProvider({ children }: { children: ReactNode }) {
  const [address, setAddressState] = useState("");
  const [input, setInput] = useState("");
  const [storeVersion, setStoreVersion] = useState(0);
  const [ready, setReady] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const last = window.localStorage.getItem(LAST_ADDR_KEY);
    const source = window.localStorage.getItem(ADDR_SOURCE_KEY);
    // 仅当来源是「手动输入」时才恢复；钱包来源或旧数据（无 source）不恢复，避免断开后重启仍看到数据
    if (last && source === "manual") {
      setAddressState(last.toLowerCase());
    } else if (last) {
      window.localStorage.removeItem(LAST_ADDR_KEY);
      window.localStorage.removeItem(ADDR_SOURCE_KEY);
    }
    setReady(true);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const handler = () => setStoreVersion((v) => v + 1);
    window.addEventListener(STORE_EVENT, handler);
    return () => window.removeEventListener(STORE_EVENT, handler);
  }, []);

  const setAddress = (addr: string, source: "wallet" | "manual" = "manual") => {
    const normalized = addr ? addr.toLowerCase() : "";
    setAddressState(normalized);
    if (typeof window !== "undefined") {
      if (normalized) {
        window.localStorage.setItem(LAST_ADDR_KEY, normalized);
        window.localStorage.setItem(ADDR_SOURCE_KEY, source);
      } else {
        window.localStorage.removeItem(LAST_ADDR_KEY);
        window.localStorage.removeItem(ADDR_SOURCE_KEY);
      }
    }
  };

  const applyInputAsAddress = () => {
    const val = input.trim();
    if (!val.startsWith("0x") || val.length < 10) {
      alert("请输入一个有效的标识（至少10个字符）");
      return;
    }
    setAddress(val, "manual");
  };

  const randomAddress = () => {
    const a = randomHex(20);
    setInput(a);
    setAddress(a, "manual");
  };

  const resetData = () => {
    if (!confirm("确认要清空所有数据吗？此操作不可恢复。")) return;
    resetStore();
    alert("✨ 数据已清空，可以重新开始你的旅程了");
  };

  const focusInput = () => {
    inputRef.current?.focus();
  };

  const value = useMemo(
    () => ({
      address,
      input,
      setInput,
      setAddress,
      applyInputAsAddress,
      randomAddress,
      resetData,
      focusInput,
      inputRef,
      storeVersion,
      ready
    }),
    [address, input, storeVersion, ready]
  );

  return <AddressContext.Provider value={value}>{children}</AddressContext.Provider>;
}

export function useAddress() {
  const ctx = useContext(AddressContext);
  if (!ctx) throw new Error("useAddress must be used within AddressProvider");
  return ctx;
}
