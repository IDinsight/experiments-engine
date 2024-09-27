import React from "react";
import { SidebarLayout } from "@/components/catalyst/sidebar-layout";
import { sidebar } from "@/components/sidebar";
import { navbar } from "@/components/navbar";
import { ProtectedComponent } from "@/components/ProtectedComponent";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ProtectedComponent>
      <SidebarLayout sidebar={sidebar()} navbar={navbar()}>
        {children}
      </SidebarLayout>
    </ProtectedComponent>
  );
}
