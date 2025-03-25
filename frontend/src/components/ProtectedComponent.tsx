"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/utils/auth";
import { usePathname, useRouter } from "next/navigation";

interface ProtectedComponentProps {
  children: React.ReactNode;
}

const ProtectedComponent: React.FC<ProtectedComponentProps> = ({
  children,
}) => {
  const router = useRouter();
  const { token } = useAuth();
  const pathname = usePathname();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    if (!token) {
      router.push("/login?sourcePage=" + encodeURIComponent(pathname));
    }
  }, [token, pathname, router]);

  // This is to prevent the page from starting to load the children before the token is checked
  useEffect(() => {
    setIsClient(true);
  }, []);
  if (!token || !isClient) {
    return null;
  } else {
    return <>{children}</>;
  }
};

export { ProtectedComponent };
