import { Suspense } from "react";
import { AuthCallback } from "./auth-callback";

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={<div className="internship-loading">Verifying email…</div>}
    >
      <AuthCallback />
    </Suspense>
  );
}
