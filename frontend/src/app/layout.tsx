import type { Metadata, Viewport } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import { SITE_URL } from "@/lib/site";
import "./globals.css";

// Body: clean, highly readable sans with Greek glyph support for bilingual text.
const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "greek"],
  display: "swap",
});

// Headers: sophisticated serif for section titles (e.g. "SIGNATURE ROLLS").
const playfair = Playfair_Display({
  variable: "--font-serif",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Masao · Asian Fusion Lounge",
    template: "%s · Masao",
  },
  description:
    "Masao Asian Fusion Lounge — sushi, bao, cocktails and shisha, made for sharing.",
  applicationName: "Masao",
  openGraph: {
    type: "website",
    siteName: "Masao",
    title: "Masao · Asian Fusion Lounge",
    description: "Sushi, bao, cocktails and shisha, made for sharing.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Masao · Asian Fusion Lounge",
    description: "Sushi, bao, cocktails and shisha, made for sharing.",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#ffffff",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="el"
      className={`${inter.variable} ${playfair.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
