import React from "react";
import { ProtectedComponent } from "@/components/ProtectedComponent";

import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ProtectedComponent>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <SiteHeader />
          <div className="mx-3 md:mx-6">{children}</div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedComponent>
  );
}
