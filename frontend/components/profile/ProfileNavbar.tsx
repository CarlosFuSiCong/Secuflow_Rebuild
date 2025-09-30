"use client";

import { Logo } from "@/components/ui/logo";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { UserMenu } from "./UserMenu";
import { getCurrentUser } from "@/lib/api/users";
import type { User } from "@/lib/types/user";

// Navigation links configuration
const NAV_LINKS = [
  { href: "/projects", label: "Projects", isActive: false },
  { href: "/profile", label: "Profile", isActive: true },
];

// Text constants
const TEXT = {
  USER_AVATAR_FALLBACK: "JD",
  MENU_MY_PROFILE: "My profile",
  MENU_ACCOUNT_SETTINGS: "Account settings",
  MENU_SIGN_OUT: "Sign out",
};

export function ProfileNavbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const resp = await getCurrentUser();
        if (resp.succeed && resp.data) {
          setUser(resp.data);
        }
      } catch (error) {
        console.error("Failed to fetch user", error);
      }
    };
    fetchUser();
  }, []);

  // Navigation Links Component
  const NavLinks = ({ isMobile = false }: { isMobile?: boolean }) => {
    const baseClasses = `font-medium ${isMobile ? "text-base" : "text-sm"} px-3 py-2 rounded-md`;

    return (
      <>
        {NAV_LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`${baseClasses} ${link.isActive
                ? "text-primary hover:bg-primary/5"
                : "text-muted-foreground hover:bg-primary/5"
              }`}
          >
            {link.label}
          </Link>
        ))}
      </>
    );
  };

  // Mobile top bar component
  const MobileTopBar = () => (
    <div
      className={`bg-background flex h-14 items-center justify-between px-4 ${!isMenuOpen ? "border-border border-b" : ""
        }`}
    >
      {/* Mobile menu toggle button */}
      <Button
        variant="ghost"
        onClick={toggleMenu}
        className="relative -ml-2 flex h-9 w-9 items-center justify-center [&_svg]:size-5"
      >
        <span
          className={`absolute transition-all duration-300 ${isMenuOpen ? "rotate-90 opacity-0" : "rotate-0 opacity-100"
            }`}
        >
          <Menu />
        </span>
        <span
          className={`absolute transition-all duration-300 ${isMenuOpen ? "rotate-0 opacity-100" : "-rotate-90 opacity-0"
            }`}
        >
          <X />
        </span>
      </Button>

      {/* Logo */}
      <Logo className="absolute left-1/2 h-8 w-8 -translate-x-1/2 transform" />

    </div>
  );

  return (
    <>
      {/* Desktop Navbar */}
      <nav className="border-border bg-background hidden h-16 border-b shadow-sm lg:block">
        <div className="container mx-auto flex h-full items-center justify-between px-6">
          {/* Left section: Logo + Navigation links */}
          <div className="flex items-center gap-x-6">
            <Logo />
            <div className="flex items-center gap-x-1">
              <NavLinks />
            </div>
          </div>
          {/* Right section: user name + user menu */}
          <div className="flex items-center gap-x-3">
            {/* User display name */}
            {user && (
              <span className="text-sm font-medium text-foreground">
                {user.display_name}
              </span>
            )}
            {/* User menu dropdown */}
            <UserMenu
              userName={user?.display_name ?? undefined}
              userEmail={user?.email}
              avatarUrl={user?.avatar || undefined}
            />
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
                <NavLinks isMobile={true} />
              </div>
            </div>
            <Separator />
            {/* Mobile user profile section */}
            <div className="p-2">
              {/* User info */}
              <div className="flex items-center space-x-3 p-2">
                <Avatar>
                  <AvatarImage
                    src={user?.avatar || "https://github.com/shadcn.png"}
                    alt="@user"
                  />
                  <AvatarFallback>
                    {user?.display_name?.substring(0, 2).toUpperCase() || TEXT.USER_AVATAR_FALLBACK}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium">{user?.display_name || "User"}</p>
                  <p className="text-muted-foreground text-sm">
                    {user?.email || ""}
                  </p>
                </div>
              </div>
              {/* User-related links */}
              <div className="space-y-1">
                <Link
                  href="/profile"
                  className="text-muted-foreground hover:bg-primary/5 block rounded-md px-2 py-2 font-medium"
                >
                  {TEXT.MENU_MY_PROFILE}
                </Link>
                <Link
                  href="#"
                  className="text-muted-foreground hover:bg-primary/5 block rounded-md px-2 py-2 font-medium"
                >
                  {TEXT.MENU_ACCOUNT_SETTINGS}
                </Link>
                <Link
                  href="#"
                  className="text-muted-foreground hover:bg-primary/5 block rounded-md px-2 py-2 font-medium"
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