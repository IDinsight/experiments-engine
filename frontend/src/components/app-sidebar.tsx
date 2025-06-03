"use client";
import * as React from "react";
import {
  LayoutDashboardIcon,
  Frame,
  Map,
  PieChart,
  Settings2,
  FlaskConicalIcon,
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

type UserDetails = {
  username: string;
  firstName: string;
  lastName: string;
  isActive: boolean;
  isVerified: boolean;
};

const getUserDetails = async (token: string | null) => {
  try {
    if (token) {
      const response = await apiCalls.getUser(token);
      if (!response) {
        throw new Error("No response from server");
      }
      return {
        username: response.username,
        firstName: response.first_name,
        lastName: response.last_name,
        isActive: response.is_active,
        isVerified: response.is_verified,
      } as UserDetails;
  } else {
    throw new Error("No token provided");
  }
} catch (error: unknown) {
    if (error instanceof Error) {
      throw new Error(`Error fetching user details: ${error.message}`);
    } else {
      throw new Error("Error fetching user details");
    }
  }
};

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
  ],
  recentExperiments: [
    {
      name: "New onboarding flows",
      url: "#",
      icon: Frame,
    },
    {
      name: "3 different voices",
      url: "#",
      icon: PieChart,
    },
    {
      name: "AI responses",
      url: "#",
      icon: Map,
    },
  ],
};
const AppSidebar = React.memo(function AppSidebar({
  ...props
}: React.ComponentProps<typeof Sidebar>) {
  const { token } = useAuth();
  const [userDetails, setUserDetails] = React.useState<UserDetails | null>(
    null
  );

  React.useEffect(() => {
    if (token) {
      getUserDetails(token)
        .then((data) => setUserDetails(data))
        .catch((error) => console.error(error));
    }
  }, [token]);
  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <WorkspaceSwitcher />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavRecentExperiments experiments={data.recentExperiments} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={userDetails} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
});

export { AppSidebar };
