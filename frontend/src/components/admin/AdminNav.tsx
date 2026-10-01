"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { logout } from "@/lib/admin-api";

const TABS = [
  { href: "/admin", label: "Μενού" },
  { href: "/admin/categories", label: "Κατηγορίες" },
];

export function AdminNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [isLeaving, setIsLeaving] = useState(false);

  async function handleLogout() {
    setIsLeaving(true);
    try {
      await logout();
      router.replace("/admin/login");
      router.refresh();
    } finally {
      setIsLeaving(false);
    }
  }

  return (
    <header className="sticky top-0 z-10 border-b border-hairline bg-background/95 backdrop-blur">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3 sm:px-6">
        <span className="font-serif text-lg font-semibold tracking-tight text-accent">
          Masao · Διαχείριση
        </span>

        <nav className="flex items-center gap-1" aria-label="Ενότητες διαχείρισης">
          {TABS.map((tab) => {
            // Το /admin είναι πρόθεμα των πάντων, οπότε θέλει ακριβές ταίριασμα.
            const isActive =
              tab.href === "/admin" ? pathname === "/admin" : pathname.startsWith(tab.href);
            return (
              <Link
                key={tab.href}
                href={tab.href}
                aria-current={isActive ? "page" : undefined}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  isActive ? "bg-accent text-white" : "text-muted hover:text-accent"
                }`}
              >
                {tab.label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center gap-3 text-sm">
          <a
            href="/menu"
            target="_blank"
            rel="noreferrer"
            className="text-muted transition-colors hover:text-accent"
          >
            Προεπισκόπηση ↗
          </a>
          <button
            type="button"
            onClick={handleLogout}
            disabled={isLeaving}
            className="text-muted transition-colors hover:text-accent disabled:opacity-50"
          >
            Αποσύνδεση
          </button>
        </div>
      </div>
    </header>
  );
}
