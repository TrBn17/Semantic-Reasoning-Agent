import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
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
