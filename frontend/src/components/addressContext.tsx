"use client";

import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { MutableRefObject, ReactNode } from "react";
import { randomHex } from "../lib/logic/proof";
import { resetStore, STORE_EVENT } from "../lib/store/localStore";

type AddressContextValue = {
  address: string;
  input: string;
  setInput: (value: string) => void;
  setAddress: (addr: string) => void;
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
    const last = window.localStorage.getItem("alive28:last_addr");
    if (last) setAddressState(last.toLowerCase());
    setReady(true);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const handler = () => setStoreVersion((v) => v + 1);
    window.addEventListener(STORE_EVENT, handler);
    return () => window.removeEventListener(STORE_EVENT, handler);
  }, []);

  const setAddress = (addr: string) => {
    const normalized = addr ? addr.toLowerCase() : "";
    setAddressState(normalized);
    if (typeof window !== "undefined") {
      if (normalized) window.localStorage.setItem("alive28:last_addr", normalized);
    }
  };

  const applyInputAsAddress = () => {
    const val = input.trim();
    if (!val.startsWith("0x") || val.length < 10) {
      alert("请输入类似 0x... 的地址（模拟也行）");
      return;
    }
    setAddress(val);
  };

  const randomAddress = () => {
    const a = randomHex(20);
    setInput(a);
    setAddress(a);
  };

  const resetData = () => {
    if (!confirm("确认清空本地数据？")) return;
    resetStore();
    alert("已清空 LocalStorage");
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
