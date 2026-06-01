import { LanguageProvider } from "@/i18n/LanguageContext";
import { MenuApp } from "@/components/MenuApp";

export default function Home() {
  return (
    <LanguageProvider>
      <MenuApp />
    </LanguageProvider>
  );
}
