import type { NextConfig } from "next";
import path from "node:path";

import { validatePublicBuildEnvironment } from "./lib/build-env";
import { publicSecurityHeaders } from "./lib/security-headers";

validatePublicBuildEnvironment(process.env, process.env.NODE_ENV);

const nextConfig: NextConfig = {
  // Standalone output is for the Docker/Cloud Run image. On Vercel (VERCEL=1) use
  // the default output so Vercel's Next.js builder manages serverless output itself.
  output: process.env.VERCEL ? undefined : "standalone",
  outputFileTracingRoot: path.join(process.cwd(), "../.."),
  poweredByHeader: false,
  // Ensure the api-client workspace package is resolved and compiled by Next in
  // monorepo builds (e.g. Vercel), not treated as an opaque external module.
  transpilePackages: ["@praxisai/api-client"],
  devIndicators: process.env.PLAYWRIGHT_TEST === "true" ? false : undefined,
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: publicSecurityHeaders(
          process.env.NEXT_PUBLIC_APP_ENV ?? process.env.APP_ENV,
          process.env.NODE_ENV,
          process.env.NEXT_PUBLIC_SUPABASE_URL,
        ),
      },
    ];
  },
};

export default nextConfig;
