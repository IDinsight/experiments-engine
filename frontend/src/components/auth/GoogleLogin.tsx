"use client";

import type React from "react";
import { useEffect, useRef, useState } from "react";

export const NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID =
  process.env.NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID || "";

interface GoogleLoginProps {
  handleCredentialResponse: (
    response: google.accounts.id.CredentialResponse
  ) => void;
  type?: "signup_with" | "signin_with" | "continue_with" | "signin";
}

const GoogleLogin: React.FC<GoogleLoginProps> = ({
  handleCredentialResponse,
  type,
}) => {
  const googleButtonRef = useRef<HTMLDivElement>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Only initialize once
    if (!isInitialized && window.google) {
      window.google.accounts.id.initialize({
        client_id: NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID,
        callback: handleCredentialResponse,
        state_cookie_domain: "https://example.com",
        auto_select: false,
      });
      setIsInitialized(true);
    }
  }, [handleCredentialResponse, isInitialized]);

  useEffect(() => {
    // Only render the button when the ref is available and Google is loaded
    if (googleButtonRef.current && window.google && isInitialized) {
      googleButtonRef.current.innerHTML = "";

      window.google.accounts.id.renderButton(googleButtonRef.current, {
        type: "standard",
        shape: "pill",
        theme: "outline",
        size: "large",
        width: 100,
        text: type ?? "signup_with",
      });
    }
  }, [type, isInitialized]);

  return <div ref={googleButtonRef} className="g-signin-button"></div>;
};

export default GoogleLogin;
