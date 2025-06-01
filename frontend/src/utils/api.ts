import { env } from "next-runtime-env";
import axios from "axios";
import { AxiosResponse, AxiosError } from "axios";

const NEXT_PUBLIC_BACKEND_URL: string =
  env("NEXT_PUBLIC_BACKEND_URL") || "http://localhost:8000";

const api = axios.create({
  baseURL: NEXT_PUBLIC_BACKEND_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response && error.response.status === 401) {
      const currentPath = window.location.pathname;
      const sourcePage = encodeURIComponent(currentPath);

      // Check if this is a workspace access error and we have a token
      if (localStorage.getItem("ee-token") &&
          (error.config?.url?.includes("/workspace/") ||
           currentPath.includes("/workspace"))) {

        window.location.href = "/workspaces";
        return Promise.resolve();
      }

      localStorage.removeItem("ee-token");
      localStorage.removeItem("ee-username");

      if (currentPath.includes("/login")) {
        return Promise.reject(error);
      } else {
        window.location.href = `/login?sourcePage=${sourcePage}`;
      }
    }
    return Promise.reject(error);
  }
);

const getUser = async (token: string) => {
  try {
    const response = await api.get("/user/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error fetching user info");
  }
};

const getLoginToken = async (username: string, password: string) => {
  const formData = new FormData();
  formData.append("username", username);
  formData.append("password", password);

  try {
    const response = await api.post("/login", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error fetching login token");
  }
};

const getGoogleLoginToken = async (idToken: {
  client_id: string;
  credential: string;
}) => {
  try {
    const response = await api.post("/login-google", idToken, {
      headers: { "Content-Type": "application/json" },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error fetching Google login token");
  }
};

const registerUser = async (
  first_name: string,
  last_name: string,
  username: string,
  password: string
) => {
  try {
    const requestBody = {
      first_name,
      last_name,
      username,
      password,
    };
    const response = await api.post("/user/", requestBody, {
      headers: {
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error registering user");
  }
};

const requestPasswordReset = async (username: string) => {
  try {
    const response = await api.post("/request-password-reset", { username });
    return response.data;
  } catch (error) {
    throw new Error("Error requesting password reset");
  }
};

const resetPassword = async (token: string, newPassword: string) => {
  try {
    const response = await api.post("/reset-password", {
      token,
      new_password: newPassword,
    });
    return response.data;
  } catch (error) {
    throw new Error("Error resetting password");
  }
};

const verifyEmail = async (token: string) => {
  try {
    const response = await api.post("/verify-email", { token });
    return response.data;
  } catch (error) {
    throw new Error("Error verifying email");
  }
};

const resendVerification = async (username: string) => {
  try {
    const response = await api.post("/resend-verification", { username });
    return response.data;
  } catch (error) {
    throw new Error("Error resending verification email");
  }
};

const getUserWorkspaces = async (token: string | null) => {
  try {
    const response = await api.get("/workspace/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error fetching user workspaces");
  }
};

const getCurrentWorkspace = async (token: string | null) => {
  try {
    const response = await api.get("/workspace/current", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error fetching current workspace");
  }
};

const switchWorkspace = async (token: string | null, workspaceName: string) => {
  try {
    const response = await api.post(
      "/workspace/switch",
      { workspace_name: workspaceName },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error("Error switching workspace");
  }
};

const createWorkspace = async (
  token: string | null,
  workspaceName: string,
  apiDailyQuota?: number,
  contentQuota?: number
) => {
  try {
    const response = await api.post(
      "/workspace/",
      {
        workspace_name: workspaceName,
        api_daily_quota: apiDailyQuota,
        content_quota: contentQuota
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error("Error creating workspace");
  }
};

const updateWorkspace = async (
  token: string | null,
  workspaceId: number,
  workspaceName?: string,
  apiDailyQuota?: number,
  contentQuota?: number
) => {
  try {
    const response = await api.put(
      `/workspace/${workspaceId}`,
      {
        workspace_name: workspaceName,
        api_daily_quota: apiDailyQuota,
        content_quota: contentQuota,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error("Error updating workspace");
  }
};

const rotateWorkspaceApiKey = async (token: string | null) => {
  try {
    const response = await api.put(
      "/workspace/rotate-key",
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error("Error rotating workspace API key");
  }
};

const getWorkspaceById = async (token: string | null, workspaceId: number) => {
  try {
    const response = await api.get(`/workspace/${workspaceId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error fetching workspace details");
  }
};

const getWorkspaceUsers = async (token: string | null, workspaceId: number) => {
  try {
    const response = await api.get(`/workspace/${workspaceId}/users`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error fetching workspace users");
  }
};

const inviteUserToWorkspace = async (
  token: string | null,
  email: string,
  workspaceName: string,
  role: string
) => {
  try {
    const response = await api.post(
      "/workspace/invite",
      {
        email,
        workspace_name: workspaceName,
        role,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error("Error inviting user to workspace");
  }
};

const removeUserFromWorkspace = async (
  token: string | null,
  workspaceId: number,
  username: string
) => {
  try {
    const response = await api.delete(
      `/workspace/${workspaceId}/users/${username}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error("Error removing user from workspace");
  }
};

const getWorkspaceKeyHistory = async (token: string | null, workspaceId: number) => {
  try {
    const response = await api.get(`/workspace/${workspaceId}/key-history`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error fetching API key history");
  }
};

export const apiCalls = {
  getUser,
  getLoginToken,
  getGoogleLoginToken,
  registerUser,
  requestPasswordReset,
  resetPassword,
  verifyEmail,
  resendVerification,
  getUserWorkspaces,
  getCurrentWorkspace,
  switchWorkspace,
  createWorkspace,
  updateWorkspace,
  rotateWorkspaceApiKey,
  getWorkspaceById,
  getWorkspaceUsers,
  inviteUserToWorkspace,
  removeUserFromWorkspace,
  getWorkspaceKeyHistory,
};
export default api;
