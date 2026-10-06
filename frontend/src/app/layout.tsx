import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Civic Education AI Lesson Planner',
  description: 'RAG Powered Lesson Plan Generator',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" style={{ backgroundColor: '#f7f3e8' }}>
      <body className="antialiased" style={{ backgroundColor: '#f7f3e8' }}>{children}</body>
    </html>
  );
}