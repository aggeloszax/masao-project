import type { Metadata } from "next";
import { LanguageProvider } from "@/i18n/LanguageContext";
import { MenuApp } from "@/components/MenuApp";
import { SelectionProvider } from "@/selection/SelectionContext";

export const metadata: Metadata = {
  title: "Menu",
  description: "Explore the Masao menu: sushi, bao, Asian fusion dishes, cocktails and shisha.",
  alternates: { canonical: "/menu" },
};

export default function MenuPage() {
  return (
    <LanguageProvider>
      <SelectionProvider>
        <MenuApp />
      </SelectionProvider>
    </LanguageProvider>
  );
}
