import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Argus — Financial Document Intelligence",
  description: "Evidence-first financial extraction with zero unflagged errors.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
