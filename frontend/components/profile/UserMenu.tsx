"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import Link from "next/link";

// Text constants
const TEXT = {
  MENU_MY_PROFILE: "My profile",
  MENU_ACCOUNT: "Account",
  MENU_SIGN_OUT: "Sign out",
  USER_AVATAR_ALT: "@user",
  USER_AVATAR_FALLBACK: "U",
};

interface UserMenuProps {
  userName?: string;
  userEmail?: string;
  avatarUrl?: string;
  onLogout?: () => void;
}

export function UserMenu({
  userName,
  userEmail,
  avatarUrl = "https://github.com/shadcn.png",
  onLogout,
}: UserMenuProps) {
  const handleLogout = () => {
    if (onLogout) {
      onLogout();
    } else {
      // Default logout behavior
      console.log("Logout clicked");
    }
  };

  // Generate fallback from userName or email
  const generateFallback = () => {
    if (userName) {
      return userName.substring(0, 2).toUpperCase();
    }
    if (userEmail) {
      return userEmail.substring(0, 2).toUpperCase();
    }
    return TEXT.USER_AVATAR_FALLBACK;
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Avatar className="cursor-pointer">
          <AvatarImage src={avatarUrl} alt={TEXT.USER_AVATAR_ALT} />
          <AvatarFallback>{generateFallback()}</AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <Link href="/profile">
          <DropdownMenuItem>{TEXT.MENU_MY_PROFILE}</DropdownMenuItem>
        </Link>
        <DropdownMenuItem>{TEXT.MENU_ACCOUNT}</DropdownMenuItem>
        <Separator className="my-1" />
        <DropdownMenuItem onClick={handleLogout}>
          {TEXT.MENU_SIGN_OUT}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}