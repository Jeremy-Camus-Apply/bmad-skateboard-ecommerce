import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Skate Assistant",
  description: "Conversational skate-equipment recommender — foundation scaffold.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
