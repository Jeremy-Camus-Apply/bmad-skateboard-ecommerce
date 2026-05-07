import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Story 1.18 may switch to "standalone" for self-hosted images.
  // Vercel handles output natively, so leave default for now.
  reactStrictMode: true,
  images: {
    // Real catalog hosts land in Story 1.7 / 1.10. Placeholder shape only.
    remotePatterns: [],
  },
};

export default nextConfig;
