import api from "@/utils/api";
import { Message } from "./types";

const getMessages = async ({ token }: { token: string | null }) => {
  try {
    const response = await api.get("/messages/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data as Message[];
  } catch (error) {
    throw error;
  }
};

const patchMessageReadStatus = async ({
  token,
  message_ids,
  is_unread,
}: {
  token: string | null;
  message_ids: number[];
  is_unread: boolean;
}) => {
  try {
    const response = await api.patch(
      "/messages/",
      {
        message_ids,
        is_unread,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );
    return response.data as Message[];
  } catch (error) {
    throw error;
  }
};

const deleteMessages = async ({
  token,
  message_ids,
}: {
  token: string | null;
  message_ids: number[];
}) => {
  try {
    const response = await api.delete("/messages/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      data: message_ids,
    });
    return response.data as Message[];
  } catch (error) {
    throw error;
  }
};
export { getMessages, patchMessageReadStatus, deleteMessages };
