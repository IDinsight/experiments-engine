import { Step } from "../types";
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

// --- A/B test types and steps ---

const ABsteps: Step[] = [
  {
    name: "addArms",
    component: AddABArms,
  },
  { name: "notifications", component: AddNotifications },
];

// --- All steps ---

const AllSteps = { mab: MABsteps, ab: ABsteps };

export { AllSteps };
