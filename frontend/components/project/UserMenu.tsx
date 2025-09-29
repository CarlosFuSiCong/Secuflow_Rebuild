import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import Link from "next/link";

interface UserMenuProps {
  isMobile?: boolean;
}

export function UserMenu({ isMobile = false }: UserMenuProps) {
  if (isMobile) {
    return (
      <div className="p-2">
        <div className="flex items-center space-x-3 p-2">
          <Avatar>
            <AvatarImage
              src="https://github.com/shadcn.png"
              alt="@shadcn"
            />
            <AvatarFallback>JD</AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium">John Doe</p>
            <p className="text-sm text-muted-foreground">
              hi@shadcndesign.com
            </p>
          </div>
        </div>
        <div>
          <Link
            href="/profile"
            className="block rounded-md px-2 py-2 font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            My profile
          </Link>
          <Link
            href="#"
            className="block rounded-md px-2 py-2 font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            Account settings
          </Link>
          <Link
            href="#"
            className="block rounded-md px-2 py-2 font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            Sign out
          </Link>
        </div>
      </div>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Avatar className="cursor-pointer">
          <AvatarImage
            src="https://github.com/shadcn.png"
            alt="@shadcn"
          />
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <Link href="/profile">
          <DropdownMenuItem>My Profile</DropdownMenuItem>
        </Link>
        <DropdownMenuItem>Account</DropdownMenuItem>
        <Separator className="my-1" />
        <DropdownMenuItem>Sign Out</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}