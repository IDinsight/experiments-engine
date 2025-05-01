"use client";
import { apiCalls } from "@/utils/api";
import { useRouter, useSearchParams } from "next/navigation";
import { ReactNode, createContext, useContext, useState, useEffect } from "react";

type AuthContextType = {
  token: string | null;
  user: string | null;
  isVerified: boolean;
  isLoading: boolean;
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
  const [isVerified, setIsVerified] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(!!getInitialToken());
  const [loginError, setLoginError] = useState<string | null>(null);

  const searchParams = useSearchParams();
  const router = useRouter();

  // Check verification status on init if token exists
  useEffect(() => {
    const checkVerificationStatus = async () => {
      const currentToken = getInitialToken();
      if (currentToken) {
        setIsLoading(true);
        try {
          const userData = await apiCalls.getUser(currentToken);
          setIsVerified(userData.is_verified);
        } catch (error) {
          console.error("Error fetching user verification status:", error);
          logout();
        } finally {
          setIsLoading(false);
        }
      }
    };

    checkVerificationStatus();
  }, []);

  const login = async (username: string, password: string) => {
    const sourcePage = searchParams.has("sourcePage")
      ? decodeURIComponent(searchParams.get("sourcePage") as string)
      : "/";

    try {
      setIsLoading(true);
      const response = await apiCalls.getLoginToken(username, password);
      const { access_token } = response;

      localStorage.setItem("ee-token", access_token);
      localStorage.setItem("ee-username", username);

      setUser(username);
      setToken(access_token);
      setLoginError(null);

      // Check if verification status is in the response
      if (response.is_verified !== undefined) {
        setIsVerified(response.is_verified);
      } else {
        // If not in response, fetch user data to get verification status
        try {
          const userData = await apiCalls.getUser(access_token);
          setIsVerified(userData.is_verified);
        } catch (error) {
          console.error("Error fetching user verification status:", error);
        }
      }

      // Redirect to verification page if not verified, otherwise to original destination
      if (response.is_verified === false) {
        router.push("/verification-required");
      } else {
        router.push(sourcePage);
      }
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
    } finally {
      setIsLoading(false);
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

    try {
      setIsLoading(true);
      const response = await apiCalls.getGoogleLoginToken({
        client_id: client_id,
        credential: credential
      });

      const { access_token, username } = response;

      localStorage.setItem("ee-token", access_token);
      localStorage.setItem("ee-username", username);

      setUser(username);
      setToken(access_token);

      setIsVerified(true);

      router.push(sourcePage);
    } catch (error) {
      setLoginError("Invalid Google credentials");
      console.error("Google login error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("ee-token");
    localStorage.removeItem("ee-accessLevel");
    localStorage.removeItem("ee-username");
    setUser(null);
    setToken(null);
    setIsVerified(false);
    router.push("/login");
  };

  const authValue: AuthContextType = {
    token,
    user,
    isVerified,
    isLoading,
    login,
    loginError,
    loginGoogle,
    logout,
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

export const useRequireVerified = () => {
  const { token, isVerified, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && token && !isVerified) {
      router.push("/verification-required");
    }
  }, [token, isVerified, isLoading, router]);

  return { token, isVerified, isLoading };
};
