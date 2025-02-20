type MethodType = "mab" | "ab";

interface Step {
  name: string;
  component: React.FC;
}

type Notification = {
  notificationTrigger: "sample" | "time" | "event";
  sampleSize?: number;
  timeDays?: number;
  eventName?: string;
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

interface StepComponentProps {
  nextStep: () => void;
  previousStep: () => void;
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
  arms: NewABArm[];
  notifications: Notification[];
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
  arms: NewMABArm[];
  notifications: Notification[];
}

interface MAB extends MABExperimentState {
  experiment_id: number;
  is_active: boolean;
  arms: MABArm[];
}

type ExperimentState = MABExperimentState | ABExperimentState;

export type {
  Step,
  Notification,
  ExperimentStateBase,
  ArmBase,
  StepComponentProps,
  MethodType,
  MABExperimentState,
  ABExperimentState,
  ExperimentState,
  MAB,
  AB,
  MABArm,
  ABArm,
};
