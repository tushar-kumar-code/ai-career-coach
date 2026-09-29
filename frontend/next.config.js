/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable double-invoking useEffects/mounts in development mode
  reactStrictMode: false,
  // Fast on-demand bundling for icon libraries and charts
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig
