import { keccak256, stringToHex } from "viem";

function getRandomValues(bytes: Uint8Array) {
  if (typeof crypto !== "undefined" && crypto.getRandomValues) {
    crypto.getRandomValues(bytes);
    return;
  }
  for (let i = 0; i < bytes.length; i += 1) {
    bytes[i] = Math.floor(Math.random() * 256);
  }
}

export function randomHex(bytes: number) {
  const arr = new Uint8Array(bytes);
  getRandomValues(arr);
  return "0x" + Array.from(arr).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export function makeSaltHex() {
  return randomHex(16);
}

export function keccakProofHash(dateKey: string, normalizedText: string, saltHex: string) {
  const joined = `${dateKey}|${normalizedText}|${saltHex}`;
  return keccak256(stringToHex(joined));
}

export function mockTxHash(seed: string) {
  return keccak256(stringToHex(seed));
}
