import { Suspense } from "react";
import { LoginForm } from "@/components/admin/LoginForm";
import { LoadingState } from "@/components/admin/ui";

export default function AdminLoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4 py-12">
      {/* useSearchParams χρειάζεται Suspense boundary στο App Router. */}
      <Suspense fallback={<LoadingState />}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
