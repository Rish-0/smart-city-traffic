import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/auth';

export const metadata: Metadata = {
  title: 'Smart City Traffic Optimisation System',
  description: 'AI-powered traffic signal optimisation, real-time monitoring, and analytics platform for smart city traffic management.',
  keywords: ['traffic', 'smart city', 'AI', 'optimization', 'monitoring', 'analytics'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚦</text></svg>" />
      </head>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
