import type { NextConfig } from "next";
import path from "node:path";

import { validatePublicBuildEnvironment } from "./lib/build-env";
import { publicSecurityHeaders } from "./lib/security-headers";

validatePublicBuildEnvironment(process.env, process.env.NODE_ENV);

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(process.cwd(), "../.."),
  poweredByHeader: false,
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
        ),
      },
    ];
  },
};

export default nextConfig;
