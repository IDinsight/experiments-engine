import api from "@/utils/api";
import { ExperimentState, MABBeta, MABNormal, CMAB, BayesianAB } from "./types";
import {
  isMABExperimentStateBeta,
  isMABExperimentStateNormal,
  isCMABExperimentState,
  isBayesianABState,
} from "./store/useExperimentStore";

const createNewExperiment = async ({
  experimentData,
  token,
}: {
  experimentData: ExperimentState;
  token: string | null;
}) => {
  const getEndpointAndData = (
    data: ExperimentState
  ): {
    endpoint: string;
  } => {

    if (isMABExperimentStateBeta(data) || isMABExperimentStateNormal(data)) {
      return { endpoint: "/mab/" };
    }

    if (isCMABExperimentState(data)) {
      return { endpoint: "/contextual_mab/" };
    }

    if (isBayesianABState(data)) {
      return { endpoint: "/bayes_ab/" };
    }

    throw new Error("Invalid experiment type");
  };

  try {
    const { endpoint } = getEndpointAndData(experimentData);
    const response = await api.post(endpoint, experimentData, {
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

const getAllMABExperiments = async (token: string | null) => {
  try {
    const response = await api.get("/mab/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    const convertedData = response.data.map(
      (experiment: MABBeta | MABNormal) => ({
        ...experiment,
        methodType: "mab",
      })
    );
    return convertedData;
  } catch (error: unknown) {
    if (error instanceof Error) {
      throw new Error(`Error fetching all experiments: ${error.message}`);
    } else {
      throw new Error("Error fetching all experiments");
    }
  }
};

const getAllCMABExperiments = async (token: string | null) => {
  try {
    const response = await api.get("/contextual_mab/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    const convertedData = response.data.map((experiment: CMAB) => ({
      ...experiment,
      methodType: "cmab",
    }));
    return convertedData;
  } catch (error: unknown) {
    if (error instanceof Error) {
      throw new Error(`Error fetching all experiments: ${error.message}`);
    } else {
      throw new Error("Error fetching all experiments");
    }
  }
};

const getAllBayesianABExperiments = async (token: string | null) => {
  try {
    const response = await api.get("/bayes_ab/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    const convertedData = response.data.map((experiment: BayesianAB) => ({
      ...experiment,
      methodType: "bayes_ab",
    }));
    return convertedData;
  } catch (error: unknown) {
    if (error instanceof Error) {
      throw new Error(`Error fetching all experiments: ${error.message}`);
    } else {
      throw new Error("Error fetching all experiments");
    }
  }
};

const getMABExperimentById = async (token: string | null, id: number) => {
  try {
    const response = await api.get(`/mab/${id}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    const convertedData = {
      ...response.data,
      methodType: "mab",
    };
    return convertedData;
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
  getAllMABExperiments,
  getAllCMABExperiments,
  getAllBayesianABExperiments,
  getMABExperimentById,
};
