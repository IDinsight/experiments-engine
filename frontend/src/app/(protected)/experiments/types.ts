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
  prior_type: PriorType;
  reward_type: RewardType;
  stickyAssignment: boolean;
  autoFail: boolean;
  autoFailValue: number;
  autoFailUnit: "days" | "hours";
}

interface ArmBase {
  name: string;
  description: string;
}

interface StepValidation {
  isValid: boolean;
  errors: Record<string, string> | Record<string, string>[];
}
// ----- Bayesian AB

interface NewBayesianABArm extends ArmBase {
  mu_init: number;
  sigma_init: number;
  is_treatment_arm: boolean;
}

interface BayesianABArm extends NewBayesianABArm {
  arm_id: number;
  mu: number;
  sigma: number;
}

interface BayesianABState extends ExperimentStateBase {
  methodType: "bayes_ab";
  arms: NewBayesianABArm[];
  notifications: Notifications;
}

interface BayesianAB extends BayesianABState {
  experiment_id: number;
  is_active: boolean;
  arms: BayesianABArm[];
}

// ----- MAB

interface NewMABArmBeta extends ArmBase {
  alpha_init: number;
  beta_init: number;
}

interface NewMABArmNormal extends ArmBase {
  mu_init: number;
  sigma_init: number;
}

interface MABArmBeta extends NewMABArmBeta {
  arm_id: number;
  alpha: number;
  beta: number;
}

interface MABArmNormal extends NewMABArmNormal {
  arm_id: number;
  mu: number;
  sigma: number;
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
  | BayesianABState;

export type {
  BayesianAB,
  BayesianABArm,
  BayesianABState,
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
  NewBayesianABArm,
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
