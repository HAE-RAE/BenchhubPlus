/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  poweredByHeader: false,
  experimental: {
    optimizePackageImports: ["lucide-react"]
  },
  // Reverse-proxy /api/* through the Next dev server to the FastAPI
  // backend. This keeps the browser on a single origin (localhost:3000)
  // so HttpOnly auth cookies and CORS just work — important for Safari
  // which treats different localhost ports as cross-site under ITP.
  async rewrites() {
    const target = process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";
    return [
      { source: "/api/:path*", destination: `${target}/api/:path*` }
    ];
  }
};

export default nextConfig;
