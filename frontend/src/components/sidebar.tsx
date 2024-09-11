import {
  Sidebar,
  SidebarBody,
  SidebarHeader,
  SidebarItem,
  SidebarLabel,
  SidebarSection,
} from "@/components/catalyst/sidebar";
import { Avatar } from "@/components/catalyst/avatar";
import { Dropdown, DropdownButton } from "@/components/catalyst/dropdown";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import TeamDropdownMenu from "@/components/TeamDropdownMenu";
import { navItems } from "@/data/navItems";
import React from "react";

export const sidebar = (): React.ReactNode => {
  return (
    <Sidebar>
      <SidebarHeader>
        <Dropdown>
          <DropdownButton as={SidebarItem} className="lg:mb-2.5">
            <Avatar src="/tailwind-logo.svg" />
            <SidebarLabel>Tailwind Labs</SidebarLabel>
            <ChevronDownIcon />
          </DropdownButton>
          <TeamDropdownMenu />
        </Dropdown>
      </SidebarHeader>
      <SidebarBody>
        <SidebarSection>
          {navItems.map(({ label, url }) => (
            <SidebarItem key={label} href={url}>
              {label}
            </SidebarItem>
          ))}
        </SidebarSection>
      </SidebarBody>
    </Sidebar>
  );
};
