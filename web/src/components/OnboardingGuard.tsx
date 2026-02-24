"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function OnboardingGuard({
  children,
}: {
  children: React.ReactNode;
}) {
  const [checked, setChecked] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Don't check on the onboarding page itself
    if (pathname === "/onboarding") {
      setChecked(true);
      return;
    }

    api
      .getMe()
      .then((user) => {
        if (user.authenticated && !user.has_completed_onboarding) {
          router.push("/onboarding");
        } else {
          setChecked(true);
        }
      })
      .catch(() => {
        // If /me fails (e.g., no auth configured), just show the app
        setChecked(true);
      });
  }, [pathname, router]);

  if (!checked) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-mako-500 animate-pulse">Loading...</p>
      </div>
    );
  }

  return <>{children}</>;
}
