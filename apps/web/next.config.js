/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ||
      'pk_test_dHJ1c3R5LW11bGxldC0zMzEwLmNsZXJrLmFjY291bnRzLmRldiQ',
  },
  output: process.env.VERCEL ? undefined : 'standalone',
  transpilePackages: ['@synapseos/ui', '@synapseos/types', '@synapseos/shared'],
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
};

module.exports = nextConfig;
