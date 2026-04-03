"use client";

import { ProfileNavbar } from "@/components/profile/ProfileNavbar";
import { ProfileSidebar } from "@/components/profile/ProfileSidebar";
import { BasicInformation } from "@/components/profile/BasicInformation";
import { SecuritySettings } from "@/components/profile/SecuritySettings";

export default function ProfilePage() {
  return (
    <div className="min-h-screen bg-background">
      <ProfileNavbar />

      <div className="container mx-auto px-4 md:px-6">
        {/* Page header */}
        <div className="py-8 border-b border-border">
          <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground mb-1">
            Account
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">Profile Settings</h1>
        </div>

        <div className="flex flex-col md:flex-row gap-8">
          <ProfileSidebar />

          <main className="flex-1 py-8 space-y-10">
            <BasicInformation />
            <SecuritySettings />
          </main>
        </div>
      </div>
    </div>
  );
}
