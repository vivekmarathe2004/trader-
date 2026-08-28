import "./globals.css";
import React from "react";
import { NavProvider } from "@/lib/nav-context";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";

export const metadata = {
  title: "VALEXIS QUANT — Autonomous Multi-Broker Trading Terminal",
  description: "Institutional deterministic quantitative trading matrix with real-time multi-pair scanning and verified execution.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-primary h-screen w-screen overflow-hidden flex font-sans antialiased selection:bg-accent selection:text-black">
        <NavProvider>
          {/* Fixed Non-Scrolling Left Sidebar */}
          <Sidebar />

          {/* Independent Scrollable Content Area */}
          <div className="flex-1 flex flex-col h-screen min-w-0 overflow-hidden">
            <Header />
            <main className="flex-1 overflow-y-auto overflow-x-hidden p-6 max-w-7xl w-full mx-auto space-y-6">
              {children}
            </main>
          </div>
        </NavProvider>
      </body>
    </html>
  );
}
