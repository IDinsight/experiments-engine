"use client";
import { apiCalls } from "@/utils/api";
import { useRouter, useSearchParams } from "next/navigation";
import { ReactNode, createContext, useContext, useState, useEffect } from "react";

type Workspace = {
  workspace_id: number;
  workspace_name: string;
  api_key_first_characters: string;
  api_daily_quota: number;
  content_quota: number;
  created_datetime_utc: string;
  updated_datetime_utc: string;
  api_key_updated_datetime_utc: string;
  is_default: boolean;
};

type AuthContextType = {
  token: string | null;
  user: string | null;
  firstName: string | null;
  lastName: string | null;
  isVerified: boolean;
  isLoading: boolean;
  currentWorkspace: Workspace | null;
  workspaces: Workspace[];
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loginError: string | null;
  loginGoogle: ({
    client_id,
    credential,
  }: {
    client_id: string;
    credential: string;
  }) => void;
  fetchWorkspaces: () => Promise<void>;
  switchWorkspace: (workspaceName: string) => Promise<void>;
  rotateWorkspaceApiKey: () => Promise<string>;
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
  const [firstName, setFirstName] = useState<string | null>(null);
  const [lastName, setLastName] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(getInitialToken);
  const [isVerified, setIsVerified] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(!!getInitialToken());
  const [loginError, setLoginError] = useState<string | null>(null);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);

  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const checkUserStatus = async () => {
      const currentToken = getInitialToken();
      if (currentToken) {
        setIsLoading(true);
        try {
          const userData = await apiCalls.getUser(currentToken);
          setIsVerified(userData.is_verified);
          setFirstName(userData.first_name);
          setLastName(userData.last_name);
          
          // Fetch current workspace
          await fetchCurrentWorkspace();

          // Fetch available workspaces
          await fetchWorkspaces();
        } catch (error) {
          console.error("Error fetching user status:", error);
          logout();
        } finally {
          setIsLoading(false);
        }
      }
    };

    checkUserStatus();
  }, []);

  const fetchCurrentWorkspace = async () => {
    if (!token) return;
    
    try {
      const workspaceData = await apiCalls.getCurrentWorkspace(token);
      setCurrentWorkspace(workspaceData);
    } catch (error) {
      console.error("Error fetching current workspace:", error);
    }
  };

  const fetchWorkspaces = async () => {
    if (!token) return;
    
    try {
      const workspacesData = await apiCalls.getUserWorkspaces(token);
      setWorkspaces(workspacesData);
    } catch (error) {
      console.error("Error fetching user workspaces:", error);
    }
  };

  const switchWorkspace = async (workspaceName: string) => {
    if (!token) return;
    
    try {
      setIsLoading(true);
      const authResponse = await apiCalls.switchWorkspace(token, workspaceName);
      
      // Update token and other auth details
      localStorage.setItem("ee-token", authResponse.access_token);
      setToken(authResponse.access_token);
      
      // Refresh workspace data
      await fetchCurrentWorkspace();
      
      return;
    } catch (error) {
      console.error("Error switching workspace:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const rotateWorkspaceApiKey = async () => {
    if (!token) throw new Error("Not authenticated");
    
    try {
      setIsLoading(true);
      const response = await apiCalls.rotateWorkspaceApiKey(token);
      
      // Update workspace to reflect key change
      await fetchCurrentWorkspace();
      
      return response.new_api_key;
    } catch (error) {
      console.error("Error rotating workspace API key:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

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
          setFirstName(userData.first_name);
          setLastName(userData.last_name);
        } catch (error) {
          console.error("Error fetching user verification status:", error);
        }
      }

      // Fetch current workspace
      try {
        const workspaceData = await apiCalls.getCurrentWorkspace(access_token);
        setCurrentWorkspace(workspaceData);
      } catch (error) {
        console.error("Error fetching current workspace:", error);
      }

      // Fetch all workspaces
      try {
        const workspacesData = await apiCalls.getUserWorkspaces(access_token);
        setWorkspaces(workspacesData);
      } catch (error) {
        console.error("Error fetching workspaces:", error);
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

      // Fetch user details
      try {
        const userData = await apiCalls.getUser(access_token);
        setIsVerified(userData.is_verified);
        setFirstName(userData.first_name);
        setLastName(userData.last_name);
      } catch (error) {
        console.error("Error fetching user details:", error);
      }

      // Fetch current workspace
      try {
        const workspaceData = await apiCalls.getCurrentWorkspace(access_token);
        setCurrentWorkspace(workspaceData);
      } catch (error) {
        console.error("Error fetching current workspace:", error);
      }

      // Fetch all workspaces
      try {
        const workspacesData = await apiCalls.getUserWorkspaces(access_token);
        setWorkspaces(workspacesData);
      } catch (error) {
        console.error("Error fetching workspaces:", error);
      }

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
    setFirstName(null);
    setLastName(null);
    setCurrentWorkspace(null);
    setWorkspaces([]);
    router.push("/login");
  };

  const authValue: AuthContextType = {
    token,
    user,
    firstName,
    lastName,
    isVerified,
    isLoading,
    currentWorkspace,
    workspaces,
    login,
    loginError,
    loginGoogle,
    logout,
    fetchWorkspaces,
    switchWorkspace,
    rotateWorkspaceApiKey,
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
