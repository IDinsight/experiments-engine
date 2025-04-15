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
      localStorage.removeItem("ee-token");
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

const registerUser = async (username: string, password: string) => {
  try {
    const requestBody = {
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
    throw new Error("Error registering user");;
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
      new_password: newPassword
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

export const apiCalls = {
  getUser,
  getLoginToken,
  getGoogleLoginToken,
  registerUser,
  requestPasswordReset,
  resetPassword,
  verifyEmail,
  resendVerification,
};
export default api;
