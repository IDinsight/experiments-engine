import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  ExperimentState,
  NewExperimentState,
  NewArm,
  PriorType,
  RewardType,
  MethodType,
  NewContext,
  Notifications
} from "../types";


export const isMABExperimentStateBeta = (experimentState: NewExperimentState) => {
  return (experimentState.prior_type === "beta" && experimentState.exp_type === "mab");
};

export const isCMABExperimentState = (experimentState: NewExperimentState) => {
  return experimentState.exp_type === "cmab";
};

export const isBayesianABState = (experimentState: NewExperimentState) => {
  return experimentState.exp_type === "bayes_ab";
};

// Define store
interface ExperimentStore {
  experimentState: NewExperimentState;

  // AI Wizard state
  aiWizardState: {
    goal: string;
    outcome: string;
    numVariants: number;
  };

  // AI Wizard updates
  updateAIGoal: (goal: string) => void;
  updateAIOutcome: (outcome: string) => void;
  updateAINumVariants: (numVariants: number) => void;
  resetAIWizardState: () => void;

  // basicInfoPage
  updateName: (name: string) => void;
  updateDescription: (description: string) => void;
  updateMethodType: (methodType: MethodType) => void;
  updateStickyAssignment: (sticky_assignment: boolean) => void;
  updateAutoFail: (auto_fail: boolean) => void;
  updateAutoFailValue: (auto_fail_value: number) => void;
  updateAutoFailUnit: (auto_fail_unit: "hours" | "days") => void;

  // Prior and reward type page
  updatePriorType: (prior_type: PriorType) => void;
  updateRewardType: (rewardType: RewardType) => void;

  // Arms updates
  updateArms: (
    arms: NewArm[]
  ) => void;
  updateArm: (
    index: number,
    arm: Partial<NewArm>
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

const createInitialState = (): NewExperimentState => {
  const baseDescr = {
    name: "",
    description: "",
    sticky_assignment: false,
    auto_fail: false,
    auto_fail_value: 10,
    auto_fail_unit: "days",
  };
  const exp_type: MethodType = "mab";
  const prior_type: PriorType = "beta";
  const reward_type: RewardType = "binary";

  const baseState = {
    ...baseDescr,
    exp_type,
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
    clients: [] as []
  };

  return {
    ...baseState,
    last_trial_datetime_utc: null,
    arms: [
      {
        name: "",
        description: "",
        alpha_init: 1,
        beta_init: 1,
        mu_init: 0,
        sigma_init: 1,
      } as NewArm,
      {
        name: "",
        description: "",
        alpha_init: 1,
        beta_init: 1,
        mu_init: 0,
        sigma_init: 1,
      } as NewArm,
    ],
    contexts: [],
  } as NewExperimentState;
};

const createInitialAIWizardState = () => ({
  goal: "",
  outcome: "",
  numVariants: 2,
});


export const useExperimentStore = create<ExperimentStore>()(
  persist(
    (set) => ({
      experimentState: createInitialState(),
      aiWizardState: createInitialAIWizardState(),

      // ------------ Basic info updates ------------
      updateName: (name: string) =>
        set((state) => ({
          experimentState: { ...state.experimentState, name },
        })),

      updateDescription: (description: string) =>
        set((state) => ({
          experimentState: { ...state.experimentState, description },
        })),

      // Add the missing AI Wizard updates
      updateAIGoal: (goal: string) =>
        set((state) => ({
          aiWizardState: { ...state.aiWizardState, goal },
        })),

      updateAIOutcome: (outcome: string) =>
        set((state) => ({
          aiWizardState: { ...state.aiWizardState, outcome },
        })),

      updateAINumVariants: (numVariants: number) =>
        set((state) => ({
          aiWizardState: { ...state.aiWizardState, numVariants },
        })),

      resetAIWizardState: () =>
        set(() => ({
          aiWizardState: createInitialAIWizardState(),
        })),

      updateStickyAssignment: (sticky_assignment: boolean) =>
        set((state) => ({
          experimentState: {
            ...state.experimentState,
            sticky_assignment,
          },
        })),

      updateAutoFail: (auto_fail: boolean) =>
        set((state) => ({
          experimentState: { ...state.experimentState, auto_fail },
        })),

      updateAutoFailValue: (auto_fail_value: number) =>
        set((state) => ({
          experimentState: {
            ...state.experimentState,
            auto_fail_value,
          },
        })),

      updateAutoFailUnit: (auto_fail_unit: "hours" | "days") =>
        set((state) => ({
          experimentState: {
            ...state.experimentState,
            auto_fail_unit,
          },
        })),

      // ------------ Method type update ------------
      updateMethodType: (newMethodType: MethodType) =>
        set((state) => {
          const { experimentState } = state;
          const { reward_type, notifications } = experimentState;

          let newState: NewExperimentState;

          if (newMethodType == "mab") {
            newState = {
              ...experimentState,
              exp_type: newMethodType,
              prior_type: "beta",
              reward_type,
              notifications,
              arms: [
                {
                  name: "",
                  description: "",
                  alpha_init: 1,
                  beta_init: 1,
                } as NewArm,
                {
                  name: "",
                  description: "",
                  alpha_init: 1,
                  beta_init: 1,
                } as NewArm,
              ],
            } as NewExperimentState;
          } else if (newMethodType == "cmab") {
            newState = {
              ...experimentState,
              exp_type: newMethodType,
              prior_type: "normal",
              reward_type,
              notifications,
              arms: [
                {
                  name: "",
                  description: "",
                  mu_init: 0,
                  sigma_init: 1,
                } as NewArm,
                {
                  name: "",
                  description: "",
                  mu_init: 0,
                  sigma_init: 1,
                } as NewArm,
              ],
              contexts: [
                {
                  name: "",
                  description: "",
                  value_type: "binary",
                } as NewContext,
              ],
            } as NewExperimentState;
          } else if (newMethodType == "bayes_ab") {
            newState = {
              ...experimentState,
              exp_type: newMethodType,
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
                } as NewArm,
                {
                  name: "",
                  description: "",
                  mu_init: 0,
                  sigma_init: 1,
                  is_treatment_arm: false,
                } as NewArm,
              ],
            } as NewExperimentState;
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
          let newState: NewExperimentState;
          const baseArm = { name: "", description: "" };

          if (experimentState.exp_type === "mab") {
            if (newPriorType === "beta") {
              newState = {
                ...experimentState,
                prior_type: newPriorType,
                arms: experimentState.arms.map(() => ({
                  ...baseArm,
                  alpha_init: 1,
                  beta_init: 1,
                })) as NewArm[],
              } as NewExperimentState;
            } else {
              newState = {
                ...experimentState,
                prior_type: newPriorType,
                arms: experimentState.arms.map(() => ({
                  ...baseArm,
                  mu_init: 0,
                  sigma_init: 1,
                })) as NewArm[],
              } as NewExperimentState;
            }
          } else if (experimentState.exp_type === "cmab") {
            newState = {
              ...experimentState,
              prior_type: newPriorType,
              arms: experimentState.arms.map(() => ({
                ...baseArm,
                mu_init: 0,
                sigma_init: 1,
              })) as NewArm[],
              contexts: (experimentState as NewExperimentState).contexts,
            } as NewExperimentState;
          } else if (experimentState.exp_type === "bayes_ab"){
            newState = {
              ...experimentState,
              prior_type: newPriorType,
              arms: experimentState.arms.map(() => ({
                ...baseArm,
                mu_init: 0,
                sigma_init: 1,
              })) as NewArm[],
            } as NewExperimentState;
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
        newArms: NewArm[]
      ) =>
        set((state) => {
          const validatedArms = newArms as NewArm[];
          return {
            experimentState: {
              ...state.experimentState,
              arms: validatedArms,
            },
          };
        }),

      updateArm: (
        index: number,
        armUpdate: Partial<NewArm>
      ) =>
        set((state) => {
          const newArms = JSON.parse(
            JSON.stringify(state.experimentState.arms)
          ) as NewArm[];
          newArms[index] = {
            ...newArms[index],
            ...(armUpdate as Partial<NewArm>),
          };
          return {
            experimentState: {
              ...state.experimentState,
              arms: newArms,
            },
          };
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
            } as NewArm;
            return {
              experimentState: {
                ...experimentState,
                arms: [...experimentState.arms, newArm],
              },
            };
          } else if (isBayesianABState(experimentState)) {
            throw new Error("Adding arms for Bayesian A/B experiments is not currently supported");
          } else {
            const newArm = {
              name: "",
              description: "",
              mu_init: 0,
              sigma_init: 1,
            } as NewArm;
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
          return {
            experimentState: {
              ...experimentState,
              arms: newArms as NewArm[],
            },
          };
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
            } as NewExperimentState,
          };
        }),

      updateContext: (index: number, contextUpdate: Partial<NewContext>) =>
        set((state) => {
          const { experimentState } = state;
          if (!isCMABExperimentState(experimentState))
            return { experimentState };

          const newContexts = [...(experimentState.contexts || [])];
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
              contexts: [...(experimentState.contexts || []), newContext],
            },
          };
        }),

      removeContext: (index: number) =>
        set((state) => {
          const { experimentState } = state;
          if (
            !isCMABExperimentState(experimentState) ||
            !experimentState.contexts ||
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
      resetState: () => set({
        experimentState: createInitialState(),
        aiWizardState: createInitialAIWizardState(), }),
    }),
    {
      name: "experiment-store", // unique name for localStorage
      storage: createJSONStorage(() => localStorage),
    }
  )
);
