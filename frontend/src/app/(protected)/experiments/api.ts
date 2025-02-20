import api from "@/utils/api";
import { MABExperimentState, ABExperimentState } from "./types";
import { ExperimentState } from "./types";

const createNewExperiment = async ({
  experimentData,
  token,
}: {
  experimentData: ExperimentState;
  token: string | null;
}) => {
  let endpoint: string;
  let newExperimentData: MABExperimentState | ABExperimentState;

  if (experimentData.methodType == "mab") {
    newExperimentData = experimentData as MABExperimentState;
    endpoint = "/mab/";
  } else if (experimentData.methodType == "ab") {
    newExperimentData = experimentData as MABExperimentState;
    endpoint = "/ab/";
  } else {
    throw new Error("Invalid experiment type");
  }

  try {
    const response = await api.post(endpoint, newExperimentData, {
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

export { createNewExperiment, getAllMABExperiments };
