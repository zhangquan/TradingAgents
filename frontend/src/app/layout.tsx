import type { Metadata } from "next";
import "./globals.css";
import { Navigation } from "@/components/navigation";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "TradingAgents - AI驱动的交易分析平台",
  description: "基于多智能体协作的专业交易分析系统，提供市场分析、新闻解读、技术指标和投资决策支持",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh" className="h-full">
      <body
        className="antialiased h-full bg-gray-50"
      >
        <div className="flex h-full">
          <Navigation />
          <main className="flex-1 lg:ml-0 pt-16 lg:pt-0 overflow-auto">
            <div className="p-6">
              {children}
            </div>
          </main>
        </div>
        <Toaster />
      </body>
    </html>
  );
}
