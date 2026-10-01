import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Διαχείριση",
  // Ο πίνακας διαχείρισης δεν έχει λόγο να βρίσκεται σε μηχανές αναζήτησης.
  robots: { index: false, follow: false },
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
