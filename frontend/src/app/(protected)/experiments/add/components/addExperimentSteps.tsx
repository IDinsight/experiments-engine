import { Step } from "../../types";
import AddMABArms from "./mabs/addMABArms";
import AddABArms from "./ab/addABArms";
import AddNotifications from "./addNotifications";

// --- MAB types and steps ---

const MABsteps: Step[] = [
  {
    name: "Add Arms",
    component: AddMABArms,
  },
  { name: "Notifications", component: AddNotifications },
];

// --- A/B test types and steps ---

const ABsteps: Step[] = [
  {
    name: "Add Arms",
    component: AddABArms,
  },
  { name: "Notifications", component: AddNotifications },
];

// --- All steps ---

const AllSteps = { mab: MABsteps, ab: ABsteps };

export { AllSteps };
