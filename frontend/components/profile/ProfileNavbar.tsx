"use client";

import { Logo } from "@/components/ui/logo";
import { Button } from "@/components/ui/button";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { UserMenu } from "./UserMenu";
import { fetchCurrentUser } from "@/lib/api/users";
import { logout } from "@/lib/api/auth";
import { useRouter } from "next/navigation";
import type { User } from "@/lib/types/user";

export function ProfileNavbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [currentPath, setCurrentPath] = useState('');
  const router = useRouter();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const resp = await fetchCurrentUser();
        if (resp.succeed && resp.data) {
          setUser(resp.data);
        }
      } catch (error) {
        console.error("Failed to fetch user", error);
      }
    };
    fetchUser();
    setCurrentPath(window.location.pathname);
  }, []);

  const handleLogout = async () => {
    await logout();
    router.push("/sign-in");
  };

  const getNavLinks = () => {
    const userId = user?.id || 'user';
    return [
      { href: `/project/${userId}/projects`, label: "Projects", isActive: currentPath.startsWith(`/project/${userId}`) },
      { href: "/profile", label: "Profile", isActive: currentPath === "/profile" },
    ];
  };

  const NavLinks = ({ isMobile = false }: { isMobile?: boolean }) => {
    const navLinks = getNavLinks();

    if (isMobile) {
      return (
        <>
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setIsMenuOpen(false)}
              className={`block text-sm font-medium py-2 px-2 transition-colors ${
                link.isActive
                  ? "text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </>
      );
    }

    return (
      <>
        {navLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`text-sm font-medium px-3 py-1 transition-colors ${
              link.isActive
                ? "text-foreground border-b-2 border-foreground pb-[calc(0.25rem-2px)]"
                : "text-muted-foreground hover:text-foreground border-b-2 border-transparent pb-[calc(0.25rem-2px)]"
            }`}
          >
            {link.label}
          </Link>
        ))}
      </>
    );
  };

  return (
    <>
      {/* Desktop Navbar */}
      <nav className="border-border bg-background hidden h-16 border-b md:block">
        <div className="container mx-auto flex h-full items-center justify-between px-6">
          <div className="flex items-center gap-x-6">
            <Logo />
            <div className="flex items-center gap-x-1">
              <NavLinks />
            </div>
          </div>
          <div className="flex items-center gap-x-3">
            {user && (
              <span className="text-sm font-medium text-foreground">
                {user.display_name}
              </span>
            )}
            <UserMenu
              userName={user?.display_name ?? undefined}
              userEmail={user?.email}
              avatarUrl={user?.avatar || undefined}
            />
          </div>
        </div>
      </nav>

      {/* Mobile top bar */}
      <nav className={`bg-background flex h-14 items-center px-4 md:hidden relative ${!isMenuOpen ? "border-b border-border" : ""}`}>
        <Button
          variant="ghost"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="relative -ml-2 flex h-9 w-9 items-center justify-center [&_svg]:size-5"
        >
          <span className={`absolute transition-all duration-200 ${isMenuOpen ? "rotate-90 opacity-0" : "rotate-0 opacity-100"}`}>
            <Menu />
          </span>
          <span className={`absolute transition-all duration-200 ${isMenuOpen ? "rotate-0 opacity-100" : "-rotate-90 opacity-0"}`}>
            <X />
          </span>
        </Button>
        <Logo className="absolute left-1/2 h-8 w-8 -translate-x-1/2" />
      </nav>

      {/* Mobile menu panel */}
      {isMenuOpen && (
        <div className="border-b border-border bg-background md:hidden">
          <div className="px-4 py-2">
            <NavLinks isMobile={true} />
          </div>
          <div className="border-t border-border px-4 py-3 flex items-center justify-between gap-4">
            <span className="text-xs text-muted-foreground truncate">
              {user?.email}
            </span>
            <button
              onClick={handleLogout}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors shrink-0"
            >
              Sign out
            </button>
          </div>
        </div>
      )}
    </>
  );
}
