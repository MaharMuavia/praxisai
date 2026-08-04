import Link from "next/link";
import { Card } from "@/components/ui";

export default function VerifyEmailPage() {
  return (
    <main className="internship-auth-page">
      <Card>
        <span className="marketing-eyebrow">Email verification</span>
        <h1>Verify the identity behind your application.</h1>
        <p>
          PraxisAI accepts only a Firebase identity with `email_verified=true`.
          Check your inbox, confirm the address, and return to the signup flow
          to continue.
        </p>
        <Link className="button button-primary" href="/auth/student-signup">
          Return to student signup
        </Link>
      </Card>
    </main>
  );
}
