import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  /** Monorepo root so Next infers one workspace (avoids multi-lockfile root warning). */
  outputFileTracingRoot: path.join(__dirname, "../.."),
  async redirects() {
    return [
      {
        source: "/chat",
        destination: "/ask",
        permanent: true,
      },
      {
        source: "/chat/:conversationId",
        destination: "/ask/:conversationId",
        permanent: true,
      },
      {
        source: "/retrieval",
        destination: "/evidence",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
