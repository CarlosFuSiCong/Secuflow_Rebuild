"use client";

import { Separator } from "@/components/ui/separator";
import { ProfileNavbar } from "@/components/profile/ProfileNavbar";
import { ProfileSidebar } from "@/components/profile/ProfileSidebar";
import { BasicInformation } from "@/components/profile/BasicInformation";
import { SecuritySettings } from "@/components/profile/SecuritySettings";

export default function ProfilePage() {
  return (
    <div className="bg-background">
      {/* Navbar */}
      <ProfileNavbar />

      <div className="container mx-auto px-4 md:px-6">
        <div className="flex flex-col md:flex-row">
          {/* Sidebar */}
          <ProfileSidebar />

          {/* Main content */}
          <main className="flex-1">
            <div className="container mx-auto px-0 py-4 md:py-6 md:pl-6">
              {/* Basic information section */}
              <BasicInformation />

              <Separator className="my-6" />

              {/* Security Settings section */}
              <SecuritySettings />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}