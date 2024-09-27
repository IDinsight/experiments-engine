import api from "@/utils/api";
import { NewMAB } from "./types";

const createMABExperiment = async ({
  mab,
  token,
}: {
  mab: NewMAB;
  token: string | null;
}) => {
  try {
    const response = await api.post("/mab/", mab, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error: any) {
    throw new Error(`Error creating new experiment: ${error.message}`);
  }
};

const getAllMABExperiments = async (token: string | null) => {
  try {
    const response = await api.get("/mab/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error: any) {
    throw new Error(`Error fetching all experiments: ${error.message}`);
  }
};

export { createMABExperiment, getAllMABExperiments };
