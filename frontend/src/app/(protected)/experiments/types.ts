type MethodType = "mab" | "cmab" | "bayes_ab";
type RewardType = "binary" | "real-valued";
type PriorType = "beta" | "normal";
type ContextType = "binary" | "real-valued";

interface BetaParams {
  name: string;
  alpha: number;
  beta: number;
}

interface GaussianParams {
  name: string;
  mu: number[];
  covariance: number[][];
}

interface StepComponentProps {
  onValidate: (validation: StepValidation) => void;
}

interface Step {
  name: string;
  component: React.FC<StepComponentProps>;
}

type Notifications = {
  onTrialCompletion?: boolean;
  numberOfTrials?: number;
  onDaysElapsed?: boolean;
  daysElapsed?: number;
  onPercentBetter?: boolean;
  percentBetterThreshold?: number;
};

interface NewContext {
  name: string;
  description: string;
  value_type: ContextType;
}

interface Context extends NewContext {
  context_id: number;
}

interface ExperimentStateBase {
  name: string;
  description: string;
  exp_type: MethodType;
  prior_type: PriorType;
  reward_type: RewardType;
  sticky_assignment: boolean;
  auto_fail: boolean;
  auto_fail_value: number;
  auto_fail_unit: "days" | "hours";
}

interface NewArm {
  name: string;
  description: string;
  mu_init?: number;
  sigma_init?: number;
  alpha_init?: number;
  beta_init?: number;
  is_treatment_arm?: boolean;
}

interface StepValidation {
  isValid: boolean;
  errors: Record<string, string> | Record<string, string>[];
}

interface Arm extends NewArm {
  arm_id: number;
  alpha?: number;
  beta?: number;
  mu?: number[];
  covariance?: number[][];
  n_outcomes: number;
}

interface NewExperimentState extends ExperimentStateBase {
  arms: NewArm[];
  notifications: Notifications;
  contexts?: NewContext[];
}

interface ExperimentState extends NewExperimentState {
  experiment_id: number;
  is_active: boolean;
  last_trial_datetime_utc: string;
  created_datetime_utc: string;
  n_trials: number;
  arms: Arm[];
  contexts?: Context[];
}


export type {
  Arm,
  BetaParams,
  Context,
  ExperimentState,
  ExperimentStateBase,
  GaussianParams,
  MethodType,
  NewArm,
  NewExperimentState,
  NewContext,
  Notifications,
  PriorType,
  RewardType,
  ContextType,
  Step,
  StepComponentProps,
  StepValidation,
};
