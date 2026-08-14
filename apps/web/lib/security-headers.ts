export type HeaderDefinition = { key: string; value: string };

export function publicSecurityHeaders(
  appEnvironment: string | undefined,
  nodeEnvironment: string | undefined = process.env.NODE_ENV,
  supabaseUrl: string | undefined = process.env.NEXT_PUBLIC_SUPABASE_URL,
) {
  const developmentEval =
    nodeEnvironment === "development" ? " 'unsafe-eval'" : "";
  let supabaseHttpSource = "";
  let supabaseWebSocketSource = "";
  if (supabaseUrl) {
    try {
      const url = new URL(supabaseUrl);
      if (url.protocol === "https:" && url.hostname) {
        supabaseHttpSource = ` ${url.origin}`;
        supabaseWebSocketSource = ` wss://${url.host}`;
      }
    } catch {
      // Hosted builds reject invalid URLs before headers are generated.
    }
  }
  const contentSecurityPolicy = [
    "default-src 'self'",
    "base-uri 'self'",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "form-action 'self'",
    `script-src 'self' 'unsafe-inline'${developmentEval}`,
    "style-src 'self' 'unsafe-inline'",
    "font-src 'self' data:",
    "img-src 'self' data: blob:",
    `connect-src 'self'${supabaseHttpSource}${supabaseWebSocketSource}`,
    `frame-src 'self'${supabaseHttpSource}`,
    "worker-src 'self' blob:",
    "manifest-src 'self'",
    "upgrade-insecure-requests",
  ].join("; ");
  const headers: HeaderDefinition[] = [
    { key: "Content-Security-Policy", value: contentSecurityPolicy },
    { key: "X-Content-Type-Options", value: "nosniff" },
    { key: "X-Frame-Options", value: "DENY" },
    {
      key: "Permissions-Policy",
      value:
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()",
    },
    { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  ];
  if (appEnvironment === "production") {
    headers.push({
      key: "Strict-Transport-Security",
      value: "max-age=31536000; includeSubDomains",
    });
  }
  return headers;
}
