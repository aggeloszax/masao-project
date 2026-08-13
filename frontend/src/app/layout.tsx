import type { Metadata, Viewport } from "next";
import { Inter, Noto_Sans_Hebrew, Playfair_Display } from "next/font/google";
import { SITE_URL } from "@/lib/site";
import "./globals.css";

// Body: clean, highly readable sans. latin-ext covers Turkish (ğ ş ı İ ç ö ü).
const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "latin-ext", "greek"],
  display: "swap",
});

// Inter has no Hebrew glyphs; this fills the gap in the font-family chain.
const notoHebrew = Noto_Sans_Hebrew({
  variable: "--font-hebrew",
  subsets: ["hebrew"],
  display: "swap",
});

// Headers: sophisticated serif for section titles (e.g. "SIGNATURE ROLLS").
const playfair = Playfair_Display({
  variable: "--font-serif",
  subsets: ["latin", "latin-ext"],
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
      className={`${inter.variable} ${notoHebrew.variable} ${playfair.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
