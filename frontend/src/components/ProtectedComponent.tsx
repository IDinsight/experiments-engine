"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/utils/auth";
import { usePathname, useRouter } from "next/navigation";

interface ProtectedComponentProps {
  children: React.ReactNode;
  requireVerified?: boolean;
}

const ProtectedComponent: React.FC<ProtectedComponentProps> = ({
  children,
  requireVerified = true,
}) => {
  const router = useRouter();
  const { token, isVerified, isLoading } = useAuth();
  const pathname = usePathname();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (isClient && !isLoading) {
      if (!token) {
        router.push("/login?sourcePage=" + encodeURIComponent(pathname));
        return;
      }

      if (requireVerified && !isVerified) {
        router.push("/verification-required");
      }
    }
  }, [token, isVerified, isLoading, requireVerified, pathname, router, isClient]);

  if (!isClient || isLoading || !token || (requireVerified && !isVerified)) {
    return null;
  } else {
    return <>{children}</>;
  }
};

export { ProtectedComponent };
