import axios from "axios";
import { AxiosResponse, AxiosError } from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response && error.response.status === 401) {
      console.log("Unauthorized request");
      const currentPath = window.location.pathname;
      const sourcePage = encodeURIComponent(currentPath);
      localStorage.removeItem("token");
      if (currentPath.includes("/login")) {
        return Promise.reject(error);
      } else {
        window.location.href = `/login?sourcePage=${sourcePage}`;
      }
    }
    return Promise.reject(error);
  },
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
    console.log(error);
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

export const apiCalls = {
  getUser,
  getLoginToken,
  getGoogleLoginToken,
};
export default api;
