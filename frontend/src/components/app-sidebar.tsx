"use client";
import * as React from "react";
import {
  AudioWaveform,
  ArrowLeftRightIcon,
  LayoutDashboardIcon,
  Command,
  Frame,
  GalleryVerticalEnd,
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
import api from "@/utils/api";
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
    const response = await api.get("/user", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return {
      username: response.data.username,
      firstName: response.data.first_name,
      lastName: response.data.last_name,
      isActive: response.data.is_active,
      isVerified: response.data.is_verified,
    } as UserDetails;
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
  workspaces: [
    {
      name: "Acme Inc",
      logo: GalleryVerticalEnd,
      plan: "Enterprise",
    },
    {
      name: "Acme Corp.",
      logo: AudioWaveform,
      plan: "Startup",
    },
    {
      name: "Evil Corp.",
      logo: Command,
      plan: "Free",
    },
  ],
  navMain: [
    {
      title: "Experiments",
      url: "/experiments",
      icon: FlaskConicalIcon,
    },
    {
      title: "Integration",
      url: "/integration",
      icon: ArrowLeftRightIcon,
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
        <WorkspaceSwitcher workspaces={data.workspaces} />
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
