import "./globals.css";
import { Providers } from "./providers";

export const metadata = {
  title: "Alive 28 MVP",
  description: "SpoonOS Graph Agent MVP"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
