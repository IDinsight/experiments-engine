"use client";

import {
  Sidebar,
  SidebarBody,
  SidebarFooter,
  SidebarHeader,
  SidebarHeading,
  SidebarItem,
  SidebarLabel,
  SidebarSection,
  SidebarSpacer,
} from "@/components/catalyst/sidebar";
import { Avatar } from "@/components/catalyst/avatar";
import { Dropdown, DropdownButton } from "@/components/catalyst/dropdown";
import { TeamDropdownMenu, AnchorProps } from "@/components/TeamDropdownMenu";
import { navItems } from "@/data/navItems";
import React from "react";
import { ChevronUpIcon } from "@heroicons/react/16/solid";
import {
  InboxIcon,
  MagnifyingGlassIcon,
  QuestionMarkCircleIcon,
  SparklesIcon,
} from "@heroicons/react/20/solid";
import { useAuth } from "@/utils/auth";

export const SidebarComponent = (): React.ReactNode => {
  const { user } = useAuth();

  return (
    <Sidebar>
      <SidebarHeader>
        <SidebarSection className="max-lg:hidden">
          <SidebarItem href="/search">
            <MagnifyingGlassIcon />
            <SidebarLabel>Search</SidebarLabel>
          </SidebarItem>
          <SidebarItem href="/inbox">
            <InboxIcon />
            <SidebarLabel>Inbox</SidebarLabel>
          </SidebarItem>
        </SidebarSection>
      </SidebarHeader>
      <SidebarBody>
        <SidebarSection>
          {navItems.map((item) => (
            <SidebarItem key={item.label} href={item.url}>
              <item.icon />
              <SidebarLabel>{item.label}</SidebarLabel>
            </SidebarItem>
          ))}
        </SidebarSection>
        <SidebarSection className="max-lg:hidden">
          <SidebarHeading>New experiments</SidebarHeading>
          <SidebarItem href="/experiments/1">
            Modifying voice of chatbot
          </SidebarItem>
          <SidebarItem href="/experiments/2">
            Different module order
          </SidebarItem>
          <SidebarItem href="/experiments/3">
            Asking feedback - 3 ways
          </SidebarItem>
          <SidebarItem href="/experiments/4">
            When to send the message
          </SidebarItem>
        </SidebarSection>
        <SidebarSpacer />
        <SidebarSection>
          <SidebarItem href="/support">
            <QuestionMarkCircleIcon />
            <SidebarLabel>Support</SidebarLabel>
          </SidebarItem>
          <SidebarItem href="/changelog">
            <SparklesIcon />
            <SidebarLabel>Changelog</SidebarLabel>
          </SidebarItem>
        </SidebarSection>
      </SidebarBody>
      <SidebarFooter className="max-lg:hidden">
        <Dropdown>
          <DropdownButton as={SidebarItem}>
            <span className="flex min-w-0 items-center gap-3">
              <Avatar initials={user?.slice(0, 2)} className="size-10" square alt="" />
              <span className="min-w-0">
                <span className="block truncate text-sm/5 font-medium text-zinc-950 dark:text-white">
                  {user}
                </span>
                <span className="block truncate text-xs/5 font-normal text-zinc-500 dark:text-zinc-400">
                  {user}
                </span>
              </span>
            </span>
            <ChevronUpIcon />
          </DropdownButton>
          <TeamDropdownMenu anchorPosition={"top start" as AnchorProps} />
        </Dropdown>
      </SidebarFooter>
    </Sidebar>
  );
};
