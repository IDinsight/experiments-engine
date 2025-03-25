"use client";

import type React from "react";
import { createContext, useContext, useState } from "react";
import { ExperimentState } from "../../types";

type ExperimentContextType = {
  experimentState: ExperimentState;
  setExperimentState: React.Dispatch<React.SetStateAction<ExperimentState>>;
};

const ExperimentContext = createContext<ExperimentContextType | undefined>(
  undefined,
);

export const useExperiment = () => {
  const context = useContext(ExperimentContext);
  if (!context) {
    throw new Error("useExperiment must be used within an ExperimentProvider");
  }
  return context;
};

export const ExperimentProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [experimentState, setExperimentState] = useState<ExperimentState>({
    name: "",
    description: "",
    methodType: "mab",
    rewardType: "binary",
    priorType: "beta",
    arms: [
      { name: "", description: "", alpha: 1, beta: 1 },
      { name: "", description: "", alpha: 1, beta: 1 },
    ],
    notifications: {
      onTrialCompletion: false,
      numberOfTrials: 0,
      onDaysElapsed: false,
      daysElapsed: 0,
      onPercentBetter: false,
      percentBetterThreshold: 0,
    },
  });

  return (
    <ExperimentContext.Provider value={{ experimentState, setExperimentState }}>
      {children}
    </ExperimentContext.Provider>
  );
};
