"use client";
import { apiCalls } from "@/utils/api";
import { useRouter, useSearchParams } from "next/navigation";
import { ReactNode, createContext, useContext, useState } from "react";

type AuthContextType = {
  token: string | null;
  user: string | null;
  login: (username: string, password: string) => void;
  logout: () => void;
  loginError: string | null;
  loginGoogle: ({
    client_id,
    credential,
  }: {
    client_id: string;
    credential: string;
  }) => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

type AuthProviderProps = {
  children: ReactNode;
};

const AuthProvider = ({ children }: AuthProviderProps) => {

  const getInitialToken = () => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("ee-token");
    }
    return null;
  };

  const getInitialUsername = () => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("ee-username");
    }
    return null;
  };

  const [user, setUser] = useState<string | null>(getInitialUsername);
  const [token, setToken] = useState<string | null>(getInitialToken);
  const [loginError, setLoginError] = useState<string | null>(null);

  const searchParams = useSearchParams();
  const router = useRouter();

  const login = async (username: string, password: string) => {
    const sourcePage = searchParams.has("sourcePage")
      ? decodeURIComponent(searchParams.get("sourcePage") as string)
      : "/";

    try {
      const { access_token } = await apiCalls.getLoginToken(username, password);
      localStorage.setItem("ee-token", access_token);
      localStorage.setItem("ee-username", username);

      setUser(username);
      setToken(access_token);
      setLoginError(null);
      router.push(sourcePage);
    } catch (error: unknown) {
      if (
        error &&
        typeof error === "object" &&
        "status" in error &&
        error.status === 401
      ) {
        setLoginError("Invalid username or password");
      } else {
        setLoginError("An unexpected error occurred. Please try again later.");
      }
    }
  };

  const loginGoogle = async ({
    client_id,
    credential,
  }: {
    client_id: string;
    credential: string;
  }) => {
    const sourcePage = searchParams.has("sourcePage") && searchParams.get("sourcePage") != ""
      ? decodeURIComponent(searchParams.get("sourcePage") as string)
      : "/";

    apiCalls
      .getGoogleLoginToken({ client_id: client_id, credential: credential })
      .then(
        ({
          access_token,
          username,
        }: {
          access_token: string;
          username: string;
        }) => {
          localStorage.setItem("ee-token", access_token);
          localStorage.setItem("ee-username", username);
          setUser(username);
          setToken(access_token);
          router.push(sourcePage);
        }
      )
      .catch((error: Error) => {
        setLoginError("Invalid Google credentials");
        console.error("Google login error:", error);
      });
  };

  const logout = () => {
    localStorage.removeItem("ee-token");
    localStorage.removeItem("ee-accessLevel");
    localStorage.removeItem("ee-username");
    setUser(null);
    setToken(null);
    router.push("/login");
  };

  const authValue: AuthContextType = {
    token: token,
    user: user,
    login: login,
    loginError: loginError,
    loginGoogle: loginGoogle,
    logout: logout,
  };

  return (
    <AuthContext.Provider value={authValue}>{children}</AuthContext.Provider>
  );
};

export default AuthProvider;

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
