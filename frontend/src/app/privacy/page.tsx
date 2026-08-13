import type { Metadata } from "next";
import { LanguageProvider } from "@/i18n/LanguageContext";
import { PrivacyContent } from "./privacy-content";

export const metadata: Metadata = {
  title: "Privacy Policy · Masao",
  description: "Privacy policy for the Masao digital menu and AI assistant.",
  robots: { index: false, follow: true },
};

export default function PrivacyPage() {
  return (
    <LanguageProvider>
      <PrivacyContent />
    </LanguageProvider>
  );
}
