"use client";

import * as React from "react";
import { ChevronsUpDown, FlaskConical } from "lucide-react";
import { useAuth } from "@/utils/auth";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import Link from "next/link";

export function WorkspaceSwitcher() {
  const { isMobile } = useSidebar();
  const { currentWorkspace, workspaces, switchWorkspace } = useAuth();
  const [isLoading, setIsLoading] = React.useState(false);

  if (!currentWorkspace) {
    return null;
  }

  const handleWorkspaceSwitch = async (workspaceName: string) => {
    if (workspaceName === currentWorkspace.workspace_name) return;

    try {
      setIsLoading(true);
      await switchWorkspace(workspaceName);
    } catch (error) {
      console.error("Error switching workspace:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild disabled={isLoading}>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                <FlaskConical className="size-4" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">
                  {currentWorkspace.workspace_name}
                </span>
                <span className="truncate text-xs">
                  {isLoading ? "Switching..." : "Workspace"}
                </span>
              </div>
              <ChevronsUpDown className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg z-100 bg-popover shadow-md"
            align="start"
            side={isMobile ? "bottom" : "right"}
            sideOffset={4}
          >
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Workspaces
            </DropdownMenuLabel>
            {workspaces.map((workspace, index) => (
              <DropdownMenuItem
                key={workspace.workspace_id}
                onClick={() => handleWorkspaceSwitch(workspace.workspace_name)}
                className={`gap-2 p-2 ${workspace.workspace_id === currentWorkspace.workspace_id ? "bg-accent" : ""}`}
              >
                <div className="flex size-6 items-center justify-center rounded-sm border">
                  <FlaskConical className="size-4 shrink-0" />
                </div>
                {workspace.workspace_name}
                <DropdownMenuShortcut>⌘{index + 1}</DropdownMenuShortcut>
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
            <DropdownMenuItem className="gap-2 p-2">
                <Link href="/workspaces" className="flex items-center gap-2 w-full">
                  <div className="flex size-6 items-center justify-center rounded-md border bg-background">
                    <span className="text-lg">+</span>
                  </div>
                  <div className="font-medium text-muted-foreground">
                    Add workspace
                  </div>
                </Link>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
