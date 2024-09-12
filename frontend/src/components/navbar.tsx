import {
  Navbar,
  NavbarItem,
  NavbarSection,
  NavbarSpacer,
} from "@/components/catalyst/navbar";
import { Avatar } from "@/components/catalyst/avatar";
import { Dropdown, DropdownButton } from "@/components/catalyst/dropdown";
import { TeamDropdownMenu, AnchorProps } from "@/components/TeamDropdownMenu";
import { InboxIcon, MagnifyingGlassIcon } from "@heroicons/react/20/solid";
import React from "react";

export const navbar = (): React.ReactNode => {
  return (
    <Navbar>
      <NavbarSpacer />
      <NavbarSection>
        <NavbarItem href="/search" aria-label="Search">
          <MagnifyingGlassIcon />
        </NavbarItem>
        <NavbarItem href="/inbox" aria-label="Inbox">
          <InboxIcon />
        </NavbarItem>
        <Dropdown>
          <DropdownButton as={NavbarItem}>
            <Avatar initials="sr" square />
          </DropdownButton>
          <TeamDropdownMenu anchorPosition={"bottom end" as AnchorProps} />
        </Dropdown>
      </NavbarSection>
    </Navbar>
  );
};
