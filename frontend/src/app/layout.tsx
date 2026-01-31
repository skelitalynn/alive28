import "./globals.css";
import type { Metadata } from "next";
import TopBar from "../components/TopBar";
import AddressBar from "../components/AddressBar";
import { AddressProvider } from "../components/addressContext";

export const metadata: Metadata = {
  title: "Alive28 - 前端纯模拟 Demo",
  description: "Alive28 纯前端模拟版"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen text-slate-900 bg-white">
        <AddressProvider>
          <div className="max-w-5xl mx-auto px-4 py-6">
            <TopBar />
            <AddressBar />
            <div className="mt-6">{children}</div>
            <div className="mt-10 text-xs text-slate-400">
              数据存储：LocalStorage key = <span className="font-mono">alive28:v1</span> · ProofHash 公式：
              <span className="font-mono">keccak256(utf8(dateKey + "|" + normalizedText + "|" + saltHex))</span>
            </div>
          </div>
        </AddressProvider>
      </body>
    </html>
  );
}
