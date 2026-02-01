import "./globals.css";
import type { Metadata } from "next";
import TopBar from "../components/TopBar";
import AddressBar from "../components/AddressBar";
import { AddressProvider } from "../components/addressContext";
import { WalletProvider } from "../components/WalletProvider";
import Cat from "../components/Cat";

export const metadata: Metadata = {
  title: "Alive28 - 28天心灵成长之旅",
  description: "每天一小步，遇见更好的自己"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen text-pink-800">
        <WalletProvider>
          <AddressProvider>
            {/* 丑猫伙伴 - 会在所有页面陪伴用户 */}
            <Cat showOnAllPages={true} initialGreeting={true} />
            <div className="max-w-5xl mx-auto px-4 py-6">
              <TopBar />
              <AddressBar />
              <div className="mt-6">{children}</div>
            </div>
          </AddressProvider>
        </WalletProvider>
      </body>
    </html>
  );
}
