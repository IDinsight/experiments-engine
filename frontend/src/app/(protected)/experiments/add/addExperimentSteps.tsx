import { Step } from "../types";
import AddMABArms from "./components/addMABArms";
import AddABArms from "./components/addABArms";
import AddNotifications from "./components/addNotifications";

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
