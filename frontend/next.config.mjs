/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://luther-spots.onrender.com/:path*',
      },
    ];
  },
};

export default nextConfig;
