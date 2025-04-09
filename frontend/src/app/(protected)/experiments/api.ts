import api from "@/utils/api";
import { ExperimentState } from "./types";
import {
  isMABExperimentStateBeta,
  isMABExperimentStateNormal,
  isCMABExperimentState,
  isABExperimentState,
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
    convertedData: Record<
      string,
      string | string[] | boolean | number | object
    >;
  } => {
    const baseData = {
      name: data.name,
      description: data.description,
      arms: data.arms,
      notifications: data.notifications,
    };

    if (isMABExperimentStateBeta(data) || isMABExperimentStateNormal(data)) {
      return {
        endpoint: "/mab/",
        convertedData: {
          ...baseData,
          reward_type: data.rewardType,
          prior_type: data.priorType,
        },
      };
    }

    if (isCMABExperimentState(data)) {
      return {
        endpoint: "/contextual_mab/",
        convertedData: {
          ...baseData,
          reward_type: data.rewardType,
          prior_type: data.priorType,
          contexts: data.contexts,
        },
      };
    }

    if (isABExperimentState(data)) {
      return {
        endpoint: "/ab/",
        convertedData: baseData,
      };
    }

    throw new Error("Invalid experiment type");
  };

  try {
    const { endpoint, convertedData } = getEndpointAndData(experimentData);
    const response = await api.post(endpoint, convertedData, {
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
      (experiment: { prior_type: string; reward_type: string }) => ({
        ...experiment,
        priorType: experiment.prior_type,
        rewardType: experiment.reward_type,
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
    const convertedData = response.data.map(
      (experiment: { prior_type: string; reward_type: string }) => ({
        ...experiment,
        priorType: experiment.prior_type,
        rewardType: experiment.reward_type,
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
  getMABExperimentById,
};
