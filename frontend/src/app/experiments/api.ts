import api from "@/utils/api";
import { NewMAB } from "./types";

const createMABExperiment = async ({ mab }: { mab: NewMAB }) => {
  try {
    const response = await api.post("/mab/", mab);
    return response.data;
  } catch (error: any) {
    throw new Error(`Error creating new experiment: ${error.message}`);
  }
};

const getAllMABExperiments = async () => {
  try {
    const response = await api.get("/mab/");
    return response.data;
  } catch (error: any) {
    throw new Error(`Error fetching all experiments: ${error.message}`);
  }
};

export { createMABExperiment, getAllMABExperiments };
