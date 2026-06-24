"use client";

import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { MutableRefObject, ReactNode } from "react";
import { randomHex } from "../lib/logic/proof";

const LAST_ADDR_KEY = "alive28:last_addr";
const ADDR_SOURCE_KEY = "alive28:addr_source"; // "wallet" | "manual"; only manual restores after reload.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type AddressContextValue = {
  address: string;
  input: string;
  setInput: (value: string) => void;
  setAddress: (addr: string, source?: "wallet" | "manual") => void;
  applyInputAsAddress: () => void;
  randomAddress: () => void;
  focusInput: () => void;
  inputRef: MutableRefObject<HTMLInputElement | null>;
  ready: boolean;
};

const AddressContext = createContext<AddressContextValue | null>(null);

export function AddressProvider({ children }: { children: ReactNode }) {
  const [address, setAddressState] = useState("");
  const [input, setInput] = useState("");
  const [ready, setReady] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const last = window.localStorage.getItem(LAST_ADDR_KEY);
    const source = window.localStorage.getItem(ADDR_SOURCE_KEY);
    const clearStoredAddress = () => {
      window.localStorage.removeItem(LAST_ADDR_KEY);
      window.localStorage.removeItem(ADDR_SOURCE_KEY);
    };
    if (!last || source !== "manual") {
      if (last) clearStoredAddress();
      setReady(true);
      return;
    }

    fetch(`${API_BASE}/health`, { cache: "no-store" })
      .then((response) => response.json())
      .then((config) => {
        if (config.demo_mode) setAddressState(last.toLowerCase());
        else clearStoredAddress();
      })
      .catch(clearStoredAddress)
      .finally(() => setReady(true));
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
      alert("请输入一个有效的标识（至少 10 个字符）");
      return;
    }
    setAddress(val, "manual");
  };

  const randomAddress = () => {
    const a = randomHex(20);
    setInput(a);
    setAddress(a, "manual");
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
      focusInput,
      inputRef,
      ready
    }),
    [address, input, ready]
  );

  return <AddressContext.Provider value={value}>{children}</AddressContext.Provider>;
}

export function useAddress() {
  const ctx = useContext(AddressContext);
  if (!ctx) throw new Error("useAddress must be used within AddressProvider");
  return ctx;
}
