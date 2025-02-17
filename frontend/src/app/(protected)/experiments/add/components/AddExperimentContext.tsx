"use client";

import type React from "react";
import { createContext, useContext, useState } from "react";
import { ExperimentState } from "../addExperimentSteps";

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
    methodType: "MAB",
    arms: [
      { name: "", description: "", alpha_prior: 1, beta_prior: 1 },
      { name: "", description: "", alpha_prior: 1, beta_prior: 1 },
    ],
    notifications: [],
  });

  return (
    <ExperimentContext.Provider value={{ experimentState, setExperimentState }}>
      {children}
    </ExperimentContext.Provider>
  );
};
