import type { Metadata } from "next";
import { MenuApp } from "@/components/MenuApp";
import { LanguageProvider } from "@/i18n/LanguageContext";
import { SelectionProvider } from "@/selection/SelectionContext";

export const metadata: Metadata = {
  title: "Menu",
  description: "Explore the Masao menu: sushi, bao, Asian fusion dishes, cocktails and shisha.",
  alternates: { canonical: "/" },
};

export default function Home() {
  return (
    <LanguageProvider>
      <SelectionProvider>
        <MenuApp />
      </SelectionProvider>
    </LanguageProvider>
  );
}
