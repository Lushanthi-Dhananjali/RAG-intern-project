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
    <html lang="en">
      <body className="antialiased bg-gray-100">{children}</body>
    </html>
  );
}