/** Shared class strings and tiny presentational pieces for the admin area. */

export const INPUT_CLASS =
  "w-full rounded-lg border border-hairline bg-white px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-accent";

export const BUTTON_PRIMARY =
  "inline-flex items-center justify-center gap-1.5 rounded-lg bg-accent px-3.5 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50";

export const BUTTON_GHOST =
  "inline-flex items-center justify-center gap-1.5 rounded-lg border border-hairline bg-white px-3.5 py-2 text-sm font-medium text-foreground transition-colors hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-50";

export const BUTTON_DANGER =
  "inline-flex items-center justify-center gap-1.5 rounded-lg border border-accent-soft px-3.5 py-2 text-sm font-medium text-accent-soft transition-colors hover:bg-accent-soft hover:text-white disabled:cursor-not-allowed disabled:opacity-50";

export const LABEL_CLASS = "block text-xs font-semibold tracking-wide text-muted uppercase";

export function Banner({
  kind,
  message,
  onDismiss,
}: {
  kind: "error" | "success";
  message: string;
  onDismiss?: () => void;
}) {
  const tone =
    kind === "error"
      ? "border-accent-soft/40 bg-accent-soft/5 text-accent-soft"
      : "border-emerald-600/30 bg-emerald-50 text-emerald-800";

  return (
    <div
      role={kind === "error" ? "alert" : "status"}
      className={`flex items-start justify-between gap-3 rounded-lg border px-3.5 py-2.5 text-sm ${tone}`}
    >
      <span>{message}</span>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Κλείσιμο"
          className="shrink-0 opacity-60 transition-opacity hover:opacity-100"
        >
          ✕
        </button>
      )}
    </div>
  );
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-1.5">
      <span className={LABEL_CLASS}>{label}</span>
      {children}
      {hint && <span className="block text-xs text-muted">{hint}</span>}
    </label>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <p className="rounded-lg border border-dashed border-hairline px-4 py-10 text-center text-sm text-muted">
      {message}
    </p>
  );
}

export function LoadingState({ message = "Φόρτωση…" }: { message?: string }) {
  return (
    <p role="status" className="px-4 py-10 text-center text-sm text-muted">
      {message}
    </p>
  );
}
