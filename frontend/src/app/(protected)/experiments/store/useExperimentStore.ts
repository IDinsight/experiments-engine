import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  ExperimentState,
  CMABExperimentState,
  NewCMABArm,
  MABExperimentStateBeta,
  MABExperimentStateNormal,
  BayesianABState,
  PriorType,
  RewardType,
  MethodType,
  NewMABArmBeta,
  NewMABArmNormal,
  NewBayesianABArm,
  NewContext,
  Notifications
} from "../types";

// Type guards for better type safety

export function isMABExperimentStateBeta(
  state: ExperimentState
): state is MABExperimentStateBeta {
  return state.methodType === "mab" && state.prior_type === "beta";
}

export function isMABExperimentStateNormal(
  state: ExperimentState
): state is MABExperimentStateNormal {
  return state.methodType === "mab" && state.prior_type === "normal";
}

export function isCMABExperimentState(
  state: ExperimentState
): state is CMABExperimentState {
  return state.methodType === "cmab";
}

export function isBayesianABState(
  state: ExperimentState
): state is BayesianABState {
  return state.methodType === "bayes_ab";
}

// Define store
interface ExperimentStore {
  experimentState: ExperimentState;

  // basicInfoPage
  updateName: (name: string) => void;
  updateDescription: (description: string) => void;
  updateMethodType: (methodType: MethodType) => void;
  updateStickyAssignment: (stickyAssignment: boolean) => void;
  updateAutoFail: (autoFail: boolean) => void;
  updateAutoFailValue: (autoFailValue: number) => void;
  updateAutoFailUnit: (autoFailUnit: "hours" | "days") => void;

  // Prior and reward type page
  updatePriorType: (prior_type: PriorType) => void;
  updateRewardType: (rewardType: RewardType) => void;

  // Arms updates
  updateArms: (
    arms: NewMABArmBeta[] | NewMABArmNormal[] | NewCMABArm[] | NewBayesianABArm[]
  ) => void;
  updateArm: (
    index: number,
    arm: Partial<NewMABArmBeta | NewMABArmNormal | NewCMABArm | NewBayesianABArm>
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
  const baseDescr = {
    name: "",
    description: "",
    stickyAssignment: false,
    autoFail: false,
    autoFailValue: 10,
    autoFailUnit: "days",
  };
  const methodType: MethodType = "mab";
  const prior_type: PriorType = "beta";
  const reward_type: RewardType = "binary";

  const baseMABState = {
    ...baseDescr,
    methodType,
    reward_type,
    prior_type,
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
      {
        name: "",
        description: "",
        alpha_init: 1,
        beta_init: 1,
      } as NewMABArmBeta,
      {
        name: "",
        description: "",
        alpha_init: 1,
        beta_init: 1,
      } as NewMABArmBeta,
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

      updateStickyAssignment: (stickyAssignment: boolean) =>
        set((state) => ({
          experimentState: {
            ...state.experimentState,
            stickyAssignment,
          },
        })),

      updateAutoFail: (autoFail: boolean) =>
        set((state) => ({
          experimentState: { ...state.experimentState, autoFail },
        })),

      updateAutoFailValue: (autoFailValue: number) =>
        set((state) => ({
          experimentState: {
            ...state.experimentState,
            autoFailValue,
          },
        })),

      updateAutoFailUnit: (autoFailUnit: "hours" | "days") =>
        set((state) => ({
          experimentState: {
            ...state.experimentState,
            autoFailUnit,
          },
        })),

      // ------------ Method type update ------------
      updateMethodType: (newMethodType: MethodType) =>
        set((state) => {
          const { experimentState } = state;
          if (newMethodType === experimentState.methodType)
            return { experimentState };

          const { reward_type, notifications } = experimentState;

          let newState: ExperimentState;

          if (newMethodType == "mab") {
            newState = {
              ...experimentState,
              methodType: newMethodType,
              prior_type: "beta",
              reward_type,
              notifications,
              arms: [
                {
                  name: "",
                  description: "",
                  alpha_init: 1,
                  beta_init: 1,
                } as NewMABArmBeta,
                {
                  name: "",
                  description: "",
                  alpha_init: 1,
                  beta_init: 1,
                } as NewMABArmBeta,
              ],
            } as MABExperimentStateBeta;
          } else if (newMethodType == "cmab") {
            newState = {
              ...experimentState,
              methodType: newMethodType,
              prior_type: "normal",
              reward_type,
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
          } else if (newMethodType == "bayes_ab") {
            newState = {
              ...experimentState,
              methodType: newMethodType,
              prior_type: "normal",
              reward_type,
              notifications,
              arms: [
                {
                  name: "",
                  description: "",
                  mu_init: 0,
                  sigma_init: 1,
                  is_treatment_arm: true,
                } as NewBayesianABArm,
                {
                  name: "",
                  description: "",
                  mu_init: 0,
                  sigma_init: 1,
                  is_treatment_arm: false,
                } as NewBayesianABArm,
              ],
            } as BayesianABState;
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
          if (newPriorType === experimentState.prior_type)
            return { experimentState };

          // Create new state based on prior type
          let newState: ExperimentState;
          const baseArm = { name: "", description: "" };

          if (experimentState.methodType === "mab") {
            if (newPriorType === "beta") {
              newState = {
                ...experimentState,
                prior_type: newPriorType,
                arms: experimentState.arms.map(() => ({
                  ...baseArm,
                  alpha_init: 1,
                  beta_init: 1,
                })) as NewMABArmBeta[],
              } as MABExperimentStateBeta;
            } else {
              newState = {
                ...experimentState,
                prior_type: newPriorType,
                arms: experimentState.arms.map(() => ({
                  ...baseArm,
                  mu_init: 0,
                  sigma_init: 1,
                })) as NewMABArmNormal[],
              } as MABExperimentStateNormal;
            }
          } else if (experimentState.methodType === "cmab") {
            newState = {
              ...experimentState,
              priorType: "normal",
              arms: experimentState.arms.map(() => ({
                ...baseArm,
                mu_init: 0,
                sigma_init: 1,
              })) as NewCMABArm[],
              contexts: (experimentState as CMABExperimentState).contexts,
            } as CMABExperimentState;
          } else if (experimentState.methodType === "bayes_ab"){
            newState = {
              ...experimentState,
              priorType: newPriorType,
              arms: experimentState.arms.map(() => ({
                ...baseArm,
                mu_init: 0,
                sigma_init: 1,
              })) as NewBayesianABArm[],
            } as BayesianABState;
          } else {
            throw new Error("Invalid method type");
          }

          return { experimentState: newState };
        }),

      // ------------  Reward type update ------------
      updateRewardType: (newRewardType: RewardType) =>
        set((state) => ({
          experimentState: {
            ...state.experimentState,
            reward_type: newRewardType,
          },
        })),

      // ------------  Arms updates ------------
      updateArms: (
        newArms: NewMABArmBeta[] | NewMABArmNormal[] | NewCMABArm[] | NewBayesianABArm[]
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
          } else if (isBayesianABState(experimentState)) {
            const validatedArms = newArms as NewBayesianABArm[];
            const updatedState: BayesianABState = {
              ...experimentState,
              arms: validatedArms,
            };
            return { experimentState: updatedState };
          } else {
            throw new Error("Invalid method type")
          }
        }),

      updateArm: (
        index: number,
        armUpdate: Partial<
          NewMABArmBeta | NewMABArmNormal | NewCMABArm | NewBayesianABArm
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
          } else if (isBayesianABState(state.experimentState)) {
            const newArms = JSON.parse(
              JSON.stringify(state.experimentState.arms)
            ) as NewBayesianABArm[];
            newArms[index] = {
              ...newArms[index],
              ...(armUpdate as Partial<NewBayesianABArm>),
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
              alpha_init: 1,
              beta_init: 1,
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
              mu_init: 0,
              sigma_init: 1,
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
          } else if (isBayesianABState(experimentState)){
            throw new Error("Adding arms for Bayesian A/B experiments is not currently supported");
          }
          return { experimentState }; // Return original state for any other case
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
          } else if (isBayesianABState(experimentState)) {
            return {
              experimentState: {
                ...experimentState,
                arms: newArms as NewBayesianABArm[],
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
