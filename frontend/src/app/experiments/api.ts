import api from "@/utils/api";
import { MAB } from "./types";

const createMABExperiment = async ({ mab }: { mab: MAB }) => {
  try {
    const response = await api.post("/mab/", mab);
    return response.data;
  } catch (error: any) {
    throw new Error(`Error creating new experiment: ${error.message}`);
  }
};

export { createMABExperiment };
