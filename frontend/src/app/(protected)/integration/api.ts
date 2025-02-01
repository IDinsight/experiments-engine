import api from "@/utils/api";

const getUser = async (token: string | null) => {
  const response = await api.get("/user/", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data;
};

const rotateAPIKey = async (token: string | null) => {
  const response = await api.put(
    "/user/rotate-key",
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
  return response.data;
};

export { getUser, rotateAPIKey };
