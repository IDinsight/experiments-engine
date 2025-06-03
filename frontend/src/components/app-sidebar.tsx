"use client";
import * as React from "react";
import {
  LayoutDashboardIcon,
  Frame,
  Map,
  PieChart,
  Settings2,
  FlaskConicalIcon
} from "lucide-react";
import { NavMain } from "@/components/nav-main";
import { NavRecentExperiments } from "@/components/nav-recent-experiments";
import { NavUser } from "@/components/nav-user";
import { WorkspaceSwitcher } from "@/components/workspace-switcher";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";
import { apiCalls } from "@/utils/api";
import { useAuth } from "@/utils/auth";

const AppSidebar: React.FC<React.ComponentProps<typeof Sidebar>> = React.memo(function AppSidebar({
  ...props
}) {
  const { user, firstName, lastName} = useAuth();

// This is sample data.
const data = {
  user: {
    name: "shadcn",
    email: "m@example.com",
    avatar: "/avatars/shadcn.jpg",
  },
  navMain: [
    {
      title: "Experiments",
      url: "/experiments",
      icon: FlaskConicalIcon,
    },
    {
      title: "Dashboard",
      url: "#",
      icon: LayoutDashboardIcon,
    },
    {
      title: "Settings",
      url: "#",
      icon: Settings2,
    },
  ]
};

  const recentExperiments = [
    {
      name: "Recent Experiment",
      url: "#",
      icon: FlaskConicalIcon
    },
    {
      name: "3 different voices",
      url: "#",
      icon: FlaskConicalIcon
    },
    {
      name: "AI responses",
      url: "#",
      icon: FlaskConicalIcon
    }
  ];

  const userDetails = {
    firstName: firstName || "?",
    lastName: lastName || "?",
    username: user || "loading"
  };

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <WorkspaceSwitcher />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavRecentExperiments experiments={recentExperiments} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={userDetails} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
});

export { AppSidebar };
