import api from "@/utils/api";
import { MABExperimentState, ABExperimentState } from "./types";
import { ExperimentState } from "./types";
import { AxiosError } from "axios";

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
    newExperimentData = experimentData as ABExperimentState;
    endpoint = "/ab/";
  } else {
    throw new Error("Invalid experiment type");
  }

  try {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { methodType, ...rest } = newExperimentData;
    console.log(rest);
    const response = await api.post(endpoint, rest, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(`Error creating new experiment: ${error.message}`);
    }
    // Handle other error types
    throw new Error(
      `Unexpected error creating new experiment: ${String(error)}`,
    );
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
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(`Error fetching all experiments: ${error.message}`);
    }
    // Handle other error types
    throw new Error(`Unexpected error fetching experiments: ${String(error)}`);
  }
};

export { createNewExperiment, getAllMABExperiments };
