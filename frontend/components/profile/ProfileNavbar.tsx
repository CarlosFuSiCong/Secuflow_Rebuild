"use client";

import { Logo } from "@/components/ui/logo";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

// Text constants
const TEXT = {
  NAV_PROJECTS: "Projects",
  NAV_PROFILE: "Profile",
  NAV_SETTINGS: "Settings",
  MENU_MY_PROFILE: "My profile",
  MENU_ACCOUNT: "Account",
  MENU_ACCOUNT_SETTINGS: "Account settings",
  MENU_SIGN_OUT: "Sign out",
  USER_NAME: "John Doe",
  USER_EMAIL: "user@secuflow.com",
  USER_AVATAR_ALT: "@shadcn",
  USER_AVATAR_FALLBACK: "JD",
};

export function ProfileNavbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  // Mobile top bar component
  const MobileTopBar = () => (
    <div
      className={`bg-background flex h-14 items-center justify-between px-4 ${
        !isMenuOpen ? "border-border border-b" : ""
      }`}
    >
      {/* Mobile menu toggle button */}
      <Button
        variant="ghost"
        onClick={toggleMenu}
        className="relative -ml-2 flex h-9 w-9 items-center justify-center [&_svg]:size-5"
      >
        <span
          className={`absolute transition-all duration-300 ${
            isMenuOpen ? "rotate-90 opacity-0" : "rotate-0 opacity-100"
          }`}
        >
          <Menu />
        </span>
        <span
          className={`absolute transition-all duration-300 ${
            isMenuOpen ? "rotate-0 opacity-100" : "-rotate-90 opacity-0"
          }`}
        >
          <X />
        </span>
      </Button>

      {/* Logo */}
      <Logo className="absolute left-1/2 h-8 w-8 -translate-x-1/2 transform" />

      {/* Mobile upgrade button */}
      <div className="absolute right-4 flex items-center gap-3">
      </div>
    </div>
  );

  // Navigation items component
  const NavItems = ({ isMobile = false }) => {
    const linkClasses = `font-medium ${isMobile ? "text-base" : "text-sm"} ${
      isMobile
        ? "text-muted-foreground"
        : "text-muted-foreground hover:bg-primary/5"
    } px-3 py-2 rounded-md`;

    return (
      <>
        {/* Main navigation links */}
        <Link href="/projects" className={linkClasses}>
          {TEXT.NAV_PROJECTS}
        </Link>
        <Link href="/profile" className={`${linkClasses} text-primary`}>
          {TEXT.NAV_PROFILE}
        </Link>
        <Link href="#" className={linkClasses}>
          {TEXT.NAV_SETTINGS}
        </Link>
      </>
    );
  };

  return (
    <>
      {/* Desktop Navbar */}
      <nav className="border-border bg-background hidden h-16 border-b shadow-sm lg:block">
        <div className="container mx-auto flex h-full items-center justify-between px-6">
          {/* Left section: Logo */}
          <div className="flex items-center gap-x-4">
            <Logo />
          </div>
          {/* Right section: user menu and button */}
          <div className="flex items-center gap-x-4">
            <div className="flex items-center gap-x-1">
              <NavItems />
            </div>
            {/* User menu dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Avatar className="cursor-pointer">
                  <AvatarImage
                    src="https://github.com/shadcn.png"
                    alt={TEXT.USER_AVATAR_ALT}
                  />
                </Avatar>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <Link href="/profile"><DropdownMenuItem>{TEXT.MENU_MY_PROFILE}</DropdownMenuItem></Link>
                <DropdownMenuItem>{TEXT.MENU_ACCOUNT}</DropdownMenuItem>
                <Separator className="my-1" />
                <DropdownMenuItem>{TEXT.MENU_SIGN_OUT}</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            {/* New item button */}
          </div>
        </div>
      </nav>

      {/* Mobile Navbar */}
      <nav className="lg:hidden">
        <MobileTopBar />
      </nav>

      {/* Mobile Menu Overlay */}
      {isMenuOpen && (
        <div className="border-border bg-background border-b lg:hidden">
          <div className="flex flex-col">
            {/* Mobile menu content */}
            <div className="flex-grow overflow-y-auto p-2">
              <div className="flex flex-col">
                <NavItems isMobile={true} />
              </div>
            </div>
            <Separator />
            {/* Mobile user profile section */}
            <div className="p-2">
              {/* User info */}
              <div className="flex items-center space-x-3 p-2">
                <Avatar>
                  <AvatarImage
                    src="https://github.com/shadcn.png"
                    alt={TEXT.USER_AVATAR_ALT}
                  />
                  <AvatarFallback>{TEXT.USER_AVATAR_FALLBACK}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium">{TEXT.USER_NAME}</p>
                  <p className="text-muted-foreground text-sm">
                    {TEXT.USER_EMAIL}
                  </p>
                </div>
              </div>
              {/* User-related links */}
              <div>
                <Link
                  href="/profile"
                  className="text-muted-foreground block rounded-md px-2 py-2 font-medium"
                >
                  {TEXT.MENU_MY_PROFILE}
                </Link>
                <Link
                  href="#"
                  className="text-muted-foreground block rounded-md px-2 py-2 font-medium"
                >
                  {TEXT.MENU_ACCOUNT_SETTINGS}
                </Link>
                <Link
                  href="#"
                  className="text-muted-foreground block rounded-md px-2 py-2 font-medium"
                >
                  {TEXT.MENU_SIGN_OUT}
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}