import { useEffect } from "react";
import { env } from "next-runtime-env";

interface GoogleLoginProps {
  handleCredentialResponse: (
    data: google.accounts.id.CredentialResponse
  ) => void;
  type: "signup_with" | "signin_with";
}

declare global {
  interface Window {
    google: typeof google;
  }
}

export const NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID: string =
  env("NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID") || "";

const GoogleLogin: React.FC<GoogleLoginProps> = ({
  handleCredentialResponse,
  type,
}) => {
  useEffect(() => {
    if (window.google) {
      window.google.accounts.id.initialize({
        client_id: NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID,
        callback: handleCredentialResponse,
        state_cookie_domain: "https://example.com",
        auto_select: false,
      });

      const signinDiv = document.getElementById("signinDiv");
      if (signinDiv) {
        window.google.accounts.id.renderButton(signinDiv, {
          type: "standard",
          shape: "pill",
          theme: "outline",
          size: "large",
          width: 100,
          text: type ?? "signup_with",
        });
      }
    }
  }, [handleCredentialResponse, type]);

  return <div id="signinDiv"></div>;
};

export default GoogleLogin;
