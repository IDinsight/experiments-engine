type MethodType = "mab" | "ab";

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

interface ExperimentStateBase {
  name: string;
  description: string;
  methodType: MethodType;
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

interface NewMABArm extends ArmBase {
  alpha_prior: number;
  beta_prior: number;
}

interface MABArm extends NewMABArm {
  arm_id: number;
  successes: number;
  failures: number;
}

interface MABExperimentState extends ExperimentStateBase {
  methodType: "mab";
  arms: NewMABArm[];
  notifications: Notifications;
}

interface MAB extends MABExperimentState {
  experiment_id: number;
  is_active: boolean;
  arms: MABArm[];
}

type ExperimentState = MABExperimentState | ABExperimentState;

export type {
  AB,
  ABArm,
  ABExperimentState,
  ArmBase,
  ExperimentState,
  ExperimentStateBase,
  MAB,
  MABArm,
  MABExperimentState,
  MethodType,
  NewABArm,
  NewMABArm,
  Notifications,
  Step,
  StepComponentProps,
  StepValidation,
};
