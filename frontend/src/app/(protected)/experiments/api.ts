import api from "@/utils/api";
import { ExperimentState, NewExperimentState } from "./types";


const createNewExperiment = async ({
  experimentData,
  token,
}: {
  experimentData: NewExperimentState;
  token: string | null;
}) => {

  try {
    const response = await api.post("/experiment", experimentData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error: unknown) {
    if (error instanceof Error) {
      throw new Error(`Error creating new experiment: ${error.message}`);
    }
    throw new Error("Error creating new experiment");
  }
};

const getExperimentsByType = async (token: string | null, exp_type: string) => {
  try {
    const response = await api.get(`/experiment/type/${exp_type}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data as ExperimentState[];
  } catch (error: unknown) {
    if (error instanceof Error) {
      throw new Error(`Error fetching all experiments: ${error.message}`);
    } else {
      throw new Error("Error fetching all experiments");
    }
  }
};

const getExperimentById = async (token: string | null, id: number) => {
  try {
    const response = await api.get(`/experiment/id/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data as ExperimentState;
  } catch (error: unknown) {
    if (error instanceof Error) {
      throw new Error(`Error fetching experiment: ${error.message}`);
    } else {
      throw new Error("Error fetching experiment");
    }
  }
};

export {
  createNewExperiment,
  getExperimentsByType,
  getExperimentById,
};
