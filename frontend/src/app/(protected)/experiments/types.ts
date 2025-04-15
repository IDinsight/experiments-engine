type MethodType = "mab" | "cmab" | "ab";
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
  mu: number;
  sigma: number;
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
  methodType: MethodType;
  priorType: PriorType;
  rewardType: RewardType;
}

interface ArmBase {
  name: string;
  description: string;
}

interface StepValidation {
  isValid: boolean;
  errors: Record<string, string> | Record<string, string>[];
}
// ----- AB

interface NewABArm extends ArmBase {
  mean_prior: number;
  stdDev_prior: number;
}

interface ABArm extends NewABArm {
  arm_id: number;
  mean_posterior: number;
  stdDev_posterior: number;
}

interface ABExperimentState extends ExperimentStateBase {
  methodType: "ab";
  arms: NewABArm[];
  notifications: Notifications;
}

interface AB extends ABExperimentState {
  experiment_id: number;
  is_active: boolean;
  arms: ABArm[];
}

// ----- MAB

interface NewMABArmBeta extends ArmBase {
  alpha: number;
  beta: number;
}

interface NewMABArmNormal extends ArmBase {
  mu: number;
  sigma: number;
}

interface MABArmBeta extends NewMABArmBeta {
  arm_id: number;
}

interface MABArmNormal extends NewMABArmNormal {
  arm_id: number;
}

interface MABExperimentStateNormal extends ExperimentStateBase {
  methodType: "mab";
  arms: NewMABArmNormal[];
  notifications: Notifications;
}

interface MABExperimentStateBeta extends ExperimentStateBase {
  methodType: "mab";
  arms: NewMABArmBeta[];
  notifications: Notifications;
}

interface MABNormal extends MABExperimentStateNormal {
  experiment_id: number;
  is_active: boolean;
  last_trial_datetime_utc: string;
  arms: MABArmNormal[];
}

interface MABBeta extends MABExperimentStateBeta {
  experiment_id: number;
  is_active: boolean;
  last_trial_datetime_utc: string;
  arms: MABArmBeta[];
}

// ----- CMAB

interface NewCMABArm extends ArmBase {
  mu_init: number;
  sigma_init: number;
}

interface CMABArm extends NewCMABArm {
  arm_id: number;
  mu: number[];
  sigma: number[];
}

interface CMABExperimentState extends ExperimentStateBase {
  methodType: "cmab";
  arms: NewCMABArm[];
  contexts: NewContext[];
  notifications: Notifications;
}

interface CMAB extends CMABExperimentState {
  experiment_id: number;
  is_active: boolean;
  arms: CMABArm[];
}

type ExperimentState =
  | MABExperimentStateNormal
  | MABExperimentStateBeta
  | CMABExperimentState
  | ABExperimentState;

export type {
  AB,
  ABArm,
  ABExperimentState,
  ArmBase,
  BetaParams,
  CMAB,
  CMABArm,
  CMABExperimentState,
  Context,
  ExperimentState,
  ExperimentStateBase,
  GaussianParams,
  MABBeta,
  MABNormal,
  MABArmBeta,
  MABArmNormal,
  MABExperimentStateBeta,
  MABExperimentStateNormal,
  MethodType,
  NewABArm,
  NewCMABArm,
  NewContext,
  NewMABArmBeta,
  NewMABArmNormal,
  Notifications,
  PriorType,
  RewardType,
  ContextType,
  Step,
  StepComponentProps,
  StepValidation,
};
