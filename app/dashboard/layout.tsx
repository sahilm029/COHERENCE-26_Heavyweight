import type { Metadata } from "next";
import Sidebar from "@/components/dashboard/Sidebar";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "ChronoReach — Dashboard",
  description: "AI-powered outreach automation dashboard",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 ml-[240px] p-6 overflow-x-hidden">
        {children}
      </main>
      <Toaster position="bottom-right" richColors />
    </div>
  );
}
