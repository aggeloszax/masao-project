"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { safeNextPath } from "@/lib/admin-auth";
import { BUTTON_PRIMARY, Banner, Field, INPUT_CLASS } from "@/components/admin/ui";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });

      if (!response.ok) {
        const payload: unknown = await response.json().catch(() => null);
        const detail =
          payload !== null && typeof payload === "object" && "detail" in payload
            ? String((payload as { detail: unknown }).detail)
            : "Η σύνδεση απέτυχε";
        setError(detail);
        return;
      }

      router.replace(safeNextPath(searchParams.get("next")));
      // Το cookie μόλις γράφτηκε: το refresh ξαναζητά το layout ως συνδεδεμένος.
      router.refresh();
    } catch {
      setError("Δεν ήταν δυνατή η επικοινωνία με τον διακομιστή");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-5">
      <div className="space-y-1.5 text-center">
        <h1 className="font-serif text-2xl font-semibold tracking-tight text-accent">
          Masao · Διαχείριση
        </h1>
        <p className="text-sm text-muted">Εισάγετε τον κωδικό για να συνεχίσετε.</p>
      </div>

      {error && <Banner kind="error" message={error} />}

      <Field label="Κωδικός">
        <input
          type="password"
          name="password"
          autoComplete="current-password"
          autoFocus
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className={INPUT_CLASS}
        />
      </Field>

      <button type="submit" disabled={isSubmitting} className={`${BUTTON_PRIMARY} w-full`}>
        {isSubmitting ? "Σύνδεση…" : "Σύνδεση"}
      </button>
    </form>
  );
}
