import type { NextConfig } from "next";
import path from "node:path";

import { validatePublicBuildEnvironment } from "./lib/build-env";

validatePublicBuildEnvironment(process.env, process.env.NODE_ENV);

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(process.cwd(), "../.."),
  poweredByHeader: false,
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
};

export default nextConfig;
