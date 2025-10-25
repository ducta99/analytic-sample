import React from 'react';
import '../globals.css';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';

export const metadata = {
  title: 'Crypto Analytics Dashboard',
  description: 'Real-time cryptocurrency analytics and portfolio tracking',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen bg-slate-950">
          <Sidebar />
          <div className="flex-1 flex flex-col">
            <Header />
            <main className="flex-1 overflow-auto p-6">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
