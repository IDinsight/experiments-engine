import { Step, Notification, ExperimentStateBase, ArmBase } from "./types";
import AddMABArms from "./components/addMABArms";
import AddABArms from "./components/addABArms";
import AddNotifications from "./components/addNotifications";

// --- MAB types and steps ---

const MABsteps: Step[] = [
  {
    name: "addArms",
    component: AddMABArms,
  },
  { name: "notifications", component: AddNotifications },
];

interface MABArm extends ArmBase {
  alpha_prior: number;
  beta_prior: number;
}

interface MABExperimentState extends ExperimentStateBase {
  arms: MABArm[];
  notifications: Notification[];
}

// --- A/B test types and steps ---

const ABsteps: Step[] = [
  {
    name: "addArms",
    component: AddABArms,
  },
  { name: "notifications", component: AddNotifications },
];

interface ABArm extends ArmBase {
  mean_prior: number;
  stdDev_prior: number;
}

interface ABExperimentState extends ExperimentStateBase {
  arms: ABArm[];
  notifications: Notification[];
}

// --- All steps ---

const AllSteps = { mab: MABsteps, ab: ABsteps };
type ExperimentState = MABExperimentState | ABExperimentState;

export { AllSteps };
export type { ExperimentState, Notification };
