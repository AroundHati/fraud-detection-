import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/ml/:path*",
        destination: "http://localhost:8000/api/ml/:path*",
      },
    ];
  },
};

export default nextConfig;
