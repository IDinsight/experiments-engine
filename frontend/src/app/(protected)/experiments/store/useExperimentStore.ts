import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  ExperimentState,
  CMABExperimentState,
  NewCMABArm,
  MABExperimentStateBeta,
  MABExperimentStateNormal,
  ABExperimentState,
  PriorType,
  RewardType,
  MethodType,
  NewMABArmBeta,
  NewMABArmNormal,
  NewABArm,
  NewContext,
  Notifications,
} from "../types";

// Type guards for better type safety

export function isMABExperimentStateBeta(
  state: ExperimentState
): state is MABExperimentStateBeta {
  return state.methodType === "mab" && state.priorType === "beta";
}

export function isMABExperimentStateNormal(
  state: ExperimentState
): state is MABExperimentStateNormal {
  return state.methodType === "mab" && state.priorType === "normal";
}

export function isCMABExperimentState(
  state: ExperimentState
): state is CMABExperimentState {
  return state.methodType === "cmab";
}

export function isABExperimentState(
  state: ExperimentState
): state is ABExperimentState {
  return state.methodType === "ab";
}

// Define store
interface ExperimentStore {
  experimentState: ExperimentState;

  // basicInfoPage
  updateName: (name: string) => void;
  updateDescription: (description: string) => void;
  updateMethodType: (methodType: MethodType) => void;

  // Prior and reward type page
  updatePriorType: (priorType: PriorType) => void;
  updateRewardType: (rewardType: RewardType) => void;

  // Arms updates
  updateArms: (
    arms: NewMABArmBeta[] | NewMABArmNormal[] | NewCMABArm[] | NewABArm[]
  ) => void;
  updateArm: (
    index: number,
    arm: Partial<NewMABArmBeta | NewMABArmNormal | NewCMABArm | NewABArm>
  ) => void;
  addArm: () => void;
  removeArm: (index: number) => void;

  // Context
  updateContexts: (contexts: NewContext[]) => void;
  updateContext: (index: number, context: Partial<NewContext>) => void;
  addContext: () => void;
  removeContext: (index: number) => void;

  // Notifications updates
  updateNotifications: (
    notifications: ExperimentState["notifications"]
  ) => void;

  // Reset state
  resetState: () => void;
}

const createInitialState = (): ExperimentState => {
  const baseDescr = { name: "", description: "" };
  const methodType: MethodType = "mab";
  const priorType: PriorType = "beta";
  const rewardType: RewardType = "binary";

  const baseMABState = {
    ...baseDescr,
    methodType,
    rewardType,
    priorType,
    notifications: {
      onTrialCompletion: false,
      numberOfTrials: 0,
      onDaysElapsed: false,
      daysElapsed: 0,
      onPercentBetter: false,
      percentBetterThreshold: 0,
    },
  };

  return {
    ...baseMABState,
    arms: [
      { name: "", description: "", alpha: 1, beta: 1 } as NewMABArmBeta,
      { name: "", description: "", alpha: 1, beta: 1 } as NewMABArmBeta,
    ],
  } as MABExperimentStateBeta;
};

export const useExperimentStore = create<ExperimentStore>()(
  persist(
    (set) => ({
      experimentState: createInitialState(),

      // ------------ Basic info updates ------------
      updateName: (name: string) =>
        set((state) => ({
          experimentState: { ...state.experimentState, name },
        })),

      updateDescription: (description: string) =>
        set((state) => ({
          experimentState: { ...state.experimentState, description },
        })),

      // ------------ Method type update ------------
      updateMethodType: (newMethodType: MethodType) =>
        set((state) => {
          const { experimentState } = state;
          if (newMethodType === experimentState.methodType)
            return { experimentState };

          const baseDescr = {
            name: experimentState.name,
            description: experimentState.description,
          };
          const { rewardType, priorType, notifications } = experimentState;

          let newState: ExperimentState;

          if (newMethodType == "mab") {
            newState = {
              ...baseDescr,
              methodType: newMethodType,
              priorType: "beta",
              rewardType,
              notifications,
              arms: [
                {
                  name: "",
                  description: "",
                  alpha: 1,
                  beta: 1,
                } as NewMABArmBeta,
                {
                  name: "",
                  description: "",
                  alpha: 1,
                  beta: 1,
                } as NewMABArmBeta,
              ],
            } as MABExperimentStateBeta;
          } else if (newMethodType == "cmab") {
            newState = {
              ...baseDescr,
              methodType: newMethodType,
              priorType: "normal",
              rewardType,
              notifications,
              arms: [
                {
                  name: "",
                  description: "",
                  mu_init: 0,
                  sigma_init: 1,
                } as NewCMABArm,
                {
                  name: "",
                  description: "",
                  mu_init: 0,
                  sigma_init: 1,
                } as NewCMABArm,
              ],
              contexts: [
                {
                  name: "",
                  description: "",
                  value_type: "binary",
                } as NewContext,
              ],
            } as CMABExperimentState;
          } else if (newMethodType == "ab") {
            newState = {
              ...baseDescr,
              methodType: newMethodType,
              priorType,
              rewardType,
              notifications,
              arms: [
                {
                  name: "",
                  description: "",
                  mean_posterior: 0,
                  stdDev_posterior: 1,
                  mean_prior: 0,
                  stdDev_prior: 1,
                } as NewABArm,
                {
                  name: "",
                  description: "",
                  mean_posterior: 0,
                  stdDev_posterior: 1,
                  mean_prior: 0,
                  stdDev_prior: 1,
                } as NewABArm,
              ],
            } as ABExperimentState;
          } else {
            throw new Error("Invalid method type");
          }
          return { experimentState: newState };
        }),

      // ------------ Prior type update ------------
      updatePriorType: (newPriorType: PriorType) =>
        set((state) => {
          const { experimentState } = state;

          // If the prior type is the same, do nothing
          if (newPriorType === experimentState.priorType)
            return { experimentState };

          // Create new state based on prior type
          const baseState = {
            name: experimentState.name,
            description: experimentState.description,
            methodType: experimentState.methodType,
            rewardType: experimentState.rewardType,
            notifications: experimentState.notifications,
            priorType: newPriorType,
          };

          let newState: ExperimentState;
          const baseArm = { name: "", description: "" };

          if (experimentState.methodType === "mab") {
            if (newPriorType === "beta") {
              newState = {
                ...baseState,
                arms: experimentState.arms.map(() => ({
                  ...baseArm,
                  alpha: 1,
                  beta: 1,
                })) as NewMABArmBeta[],
              } as MABExperimentStateBeta;
            } else {
              newState = {
                ...baseState,
                arms: experimentState.arms.map(() => ({
                  ...baseArm,
                  mu: 0,
                  sigma: 1,
                })) as NewMABArmNormal[],
              } as MABExperimentStateNormal;
            }
          } else if (experimentState.methodType === "cmab") {
            newState = {
              ...baseState,
              priorType: "normal",
              arms: experimentState.arms.map(() => ({
                ...baseArm,
                mu_init: 0,
                sigma_init: 1,
              })) as NewCMABArm[],
              contexts: (experimentState as CMABExperimentState).contexts,
            } as CMABExperimentState;
          } else {
            newState = {
              ...baseState,
              arms: experimentState.arms.map(() => ({
                ...baseArm,
                mean_posterior: 0,
                stdDev_posterior: 1,
                mean_prior: 0,
                stdDev_prior: 1,
              })) as NewABArm[],
            } as ABExperimentState;
          }

          return { experimentState: newState };
        }),

      // ------------  Reward type update ------------
      updateRewardType: (newRewardType: RewardType) =>
        set((state) => ({
          experimentState: {
            ...state.experimentState,
            rewardType: newRewardType,
          },
        })),

      // ------------  Arms updates ------------
      updateArms: (
        newArms: NewMABArmBeta[] | NewMABArmNormal[] | NewCMABArm[] | NewABArm[]
      ) =>
        set((state) => {
          const { experimentState } = state;
          if (isMABExperimentStateBeta(experimentState)) {
            const validatedArms = newArms as NewMABArmBeta[];
            const updatedState: MABExperimentStateBeta = {
              ...experimentState,
              arms: validatedArms,
            };
            return { experimentState: updatedState };
          } else if (isMABExperimentStateNormal(experimentState)) {
            const validatedArms = newArms as NewMABArmNormal[];
            const updatedState: MABExperimentStateNormal = {
              ...experimentState,
              arms: validatedArms,
            };
            return { experimentState: updatedState };
          } else if (isCMABExperimentState(experimentState)) {
            const validatedArms = newArms as NewCMABArm[];
            const updatedState: CMABExperimentState = {
              ...experimentState,
              arms: validatedArms,
            };
            return { experimentState: updatedState };
          } else {
            const validatedArms = newArms as NewABArm[];
            const updatedState: ABExperimentState = {
              ...experimentState,
              arms: validatedArms,
            };
            return { experimentState: updatedState };
          }
        }),

      updateArm: (
        index: number,
        armUpdate: Partial<
          NewMABArmBeta | NewMABArmNormal | NewCMABArm | NewABArm
        >
      ) =>
        set((state) => {
          if (isMABExperimentStateBeta(state.experimentState)) {
            const newArms = JSON.parse(
              JSON.stringify(state.experimentState.arms)
            ) as NewMABArmBeta[];
            newArms[index] = {
              ...newArms[index],
              ...(armUpdate as Partial<NewMABArmBeta>),
            };
            return {
              experimentState: { ...state.experimentState, arms: newArms },
            };
          } else if (isMABExperimentStateNormal(state.experimentState)) {
            const newArms = JSON.parse(
              JSON.stringify(state.experimentState.arms)
            ) as NewMABArmNormal[];
            newArms[index] = {
              ...newArms[index],
              ...(armUpdate as Partial<NewMABArmNormal>),
            };
            return {
              experimentState: { ...state.experimentState, arms: newArms },
            };
          } else if (isCMABExperimentState(state.experimentState)) {
            const newArms = JSON.parse(
              JSON.stringify(state.experimentState.arms)
            ) as NewCMABArm[];
            newArms[index] = {
              ...newArms[index],
              ...(armUpdate as Partial<NewCMABArm>),
            };
            return {
              experimentState: { ...state.experimentState, arms: newArms },
            };
          } else if (isABExperimentState(state.experimentState)) {
            const newArms = JSON.parse(
              JSON.stringify(state.experimentState.arms)
            ) as NewABArm[];
            newArms[index] = {
              ...newArms[index],
              ...(armUpdate as Partial<NewABArm>),
            };
            return {
              experimentState: { ...state.experimentState, arms: newArms },
            };
          } else {
            throw new Error("Invalid method type");
          }
        }),

      addArm: () =>
        set((state) => {
          const { experimentState } = state;
          if (isMABExperimentStateBeta(experimentState)) {
            const newArm = {
              name: "",
              description: "",
              alpha: 1,
              beta: 1,
            } as NewMABArmBeta;
            return {
              experimentState: {
                ...experimentState,
                arms: [...experimentState.arms, newArm],
              },
            };
          } else if (isMABExperimentStateNormal(experimentState)) {
            const newArm = {
              name: "",
              description: "",
              mu: 0,
              sigma: 1,
            } as NewMABArmNormal;
            return {
              experimentState: {
                ...experimentState,
                arms: [...experimentState.arms, newArm],
              },
            };
          } else if (isCMABExperimentState(experimentState)) {
            const newArm = {
              name: "",
              description: "",
              mu_init: 0,
              sigma_init: 1,
            } as NewCMABArm;
            return {
              experimentState: {
                ...experimentState,
                arms: [...experimentState.arms, newArm],
              },
            };
          } else {
            const newArm = {
              name: "",
              description: "",
              mean_posterior: 0,
              stdDev_posterior: 1,
              mean_prior: 0,
              stdDev_prior: 1,
            } as NewABArm;
            return {
              experimentState: {
                ...experimentState,
                arms: [...experimentState.arms, newArm],
              },
            };
          }
        }),

      removeArm: (index: number) =>
        set((state) => {
          const { experimentState } = state;
          if (experimentState.arms.length <= 2) return { experimentState };

          const newArms = [...experimentState.arms];
          newArms.splice(index, 1);
          if (isMABExperimentStateBeta(experimentState)) {
            return {
              experimentState: {
                ...experimentState,
                arms: newArms as NewMABArmBeta[],
              },
            };
          } else if (isMABExperimentStateNormal(experimentState)) {
            return {
              experimentState: {
                ...experimentState,
                arms: newArms as NewMABArmNormal[],
              },
            };
          } else if (isCMABExperimentState(experimentState)) {
            return {
              experimentState: {
                ...experimentState,
                arms: newArms as NewCMABArm[],
              },
            };
          } else if (isABExperimentState(experimentState)) {
            return {
              experimentState: {
                ...experimentState,
                arms: newArms as NewABArm[],
              },
            };
          } else {
            throw new Error("Invalid method type");
          }
        }),

      // ------------ Context updates ------------
      updateContexts: (newContexts: NewContext[]) =>
        set((state) => {
          const { experimentState } = state;
          if (!isCMABExperimentState(experimentState))
            return { experimentState };

          return {
            experimentState: {
              ...experimentState,
              contexts: newContexts,
            } as CMABExperimentState,
          };
        }),

      updateContext: (index: number, contextUpdate: Partial<NewContext>) =>
        set((state) => {
          const { experimentState } = state;
          if (!isCMABExperimentState(experimentState))
            return { experimentState };

          const newContexts = [...experimentState.contexts];
          newContexts[index] = { ...newContexts[index], ...contextUpdate };

          return {
            experimentState: {
              ...experimentState,
              contexts: newContexts,
            },
          };
        }),

      addContext: () =>
        set((state) => {
          const { experimentState } = state;
          if (!isCMABExperimentState(experimentState))
            return { experimentState };

          const newContext = {
            name: "",
            description: "",
            value_type: "binary",
          } as NewContext;

          return {
            experimentState: {
              ...experimentState,
              contexts: [...experimentState.contexts, newContext],
            },
          };
        }),

      removeContext: (index: number) =>
        set((state) => {
          const { experimentState } = state;
          if (
            !isCMABExperimentState(experimentState) ||
            experimentState.contexts.length <= 1
          )
            return { experimentState };

          const newContexts = [...experimentState.contexts];
          newContexts.splice(index, 1);

          return {
            experimentState: {
              ...experimentState,
              contexts: newContexts,
            },
          };
        }),

      // ---------------- Notifications updates ----------------
      updateNotifications: (notifications: Notifications) =>
        set((state) => ({
          experimentState: { ...state.experimentState, notifications },
        })),

      // ---------------- Reset state ----------------
      resetState: () => set({ experimentState: createInitialState() }),
    }),
    {
      name: "experiment-store", // unique name for localStorage
      storage: createJSONStorage(() => localStorage),
    }
  )
);
