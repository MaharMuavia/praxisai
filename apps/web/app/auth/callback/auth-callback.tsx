"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Brand } from "@/components/brand";
import { Card } from "@/components/ui";
import { safeAuthCallbackDestination } from "@/lib/auth-redirect";
import { getSupabaseClient } from "@/lib/supabase";

export function AuthCallback() {
  const router = useRouter();
  const params = useSearchParams();
  const started = useRef(false);
  const [callbackError, setCallbackError] = useState<string | null>(null);
  const code = params.get("code")?.trim() ?? "";
  const destination = safeAuthCallbackDestination(params.get("next"));
  const error = code
    ? callbackError
    : "The email verification link is missing or invalid.";

  useEffect(() => {
    if (!code || started.current) return;
    started.current = true;

    let active = true;
    async function completeVerification() {
      try {
        const { error: exchangeError } =
          await getSupabaseClient().auth.exchangeCodeForSession(code);
        if (!active) return;
        if (exchangeError) {
          setCallbackError(
            "The email verification link is invalid or expired.",
          );
          return;
        }
        router.replace(destination);
      } catch {
        if (active) {
          setCallbackError("Email verification is temporarily unavailable.");
        }
      }
    }

    void completeVerification();
    return () => {
      active = false;
    };
  }, [code, destination, router]);

  return (
    <main className="internship-auth-page">
      <Card>
        <Brand />
        <span className="marketing-eyebrow">Email verification</span>
        <h1>Completing your verified identity.</h1>
        {error ? (
          <>
            <p className="error" role="alert">
              {error}
            </p>
            <Link className="button button-primary" href="/auth/student-signup">
              Restart verification
            </Link>
          </>
        ) : (
          <p role="status">
            Verifying the one-time Supabase authorization code…
          </p>
        )}
      </Card>
    </main>
  );
}
