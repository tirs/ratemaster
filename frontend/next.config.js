/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    // API_BACKEND for Docker (server-side proxy); NEXT_PUBLIC_API_BACKEND for client/build
    const backend =
      process.env.API_BACKEND ||
      process.env.NEXT_PUBLIC_API_BACKEND ||
      "http://localhost:30080";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backend}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
