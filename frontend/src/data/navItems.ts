import {
  BeakerIcon,
  ArrowsRightLeftIcon,
  ChartBarIcon,
  Cog8ToothIcon,
} from "@heroicons/react/20/solid";

type NavItem = {
  label: string;
  url: string;
  icon: React.ElementType; // This ensures the icon can be used as a JSX element
};

export const navItems: NavItem[] = [
  { label: "Experiments", url: "/", icon: BeakerIcon },
  { label: "Integration", url: "/integration", icon: ArrowsRightLeftIcon },
  { label: "Dashboard", url: "/dashboard", icon: ChartBarIcon },
  { label: "Settings", url: "/settings", icon: Cog8ToothIcon },
];
