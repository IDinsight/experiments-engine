import React from "react";
import { SidebarLayout } from "@/components/catalyst/sidebar-layout";
import { SidebarComponent } from "@/components/sidebar";
import { navbar } from "@/components/navbar";
import { ProtectedComponent } from "@/components/ProtectedComponent";
import { Toaster } from "@/components/ui/toaster";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ProtectedComponent>
      <SidebarLayout sidebar={<SidebarComponent />} navbar={navbar()}>
        {children}
      </SidebarLayout>

      <Toaster />
    </ProtectedComponent>
  );
}
