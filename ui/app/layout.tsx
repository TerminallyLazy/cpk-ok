import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Script from "next/script";
import { StagewiseToolbar } from "@stagewise/toolbar-next";
const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Our Kidz Healthcare Assistant",
  description: "A healthcare assistant for parents using CopilotKit to find pediatricians, urgent care, and manage children's health profiles",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const stagewiseConfig = {
    plugins: []
  };
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
        <Script
          src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
          integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
          crossOrigin=""
        />
      </head>
      <body className={inter.className}>
        {process.env.NODE_ENV === 'development' && (
          <StagewiseToolbar config={stagewiseConfig} />
        )}
        {children}
      </body>
    </html>
  );
}
