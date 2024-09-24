"use client";

import { useAuth } from "@/utils/auth";
import { useEffect } from "react";

export default function LogoutPage() {
  const { logout } = useAuth();
  useEffect(() => {
    logout();
  }, [logout]);
  window.location.href = "/";
}
