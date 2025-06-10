import { MethodType, Step } from "../../types";
import PriorRewardSelection  from "./addPriorReward";
import AddContext from "./addContext";
import AddArms from "./addArms";
// import AddMABArms from "./mabs/addMABArms";
// import MABPriorRewardSelection from "./mabs/addPriorReward";
// import AddCMABArms from "./cmabs/addCMABArms";
// import AddCMABContexts from "./cmabs/addCMABContext";
// import CMABPriorRewardSelection from "./cmabs/addPriorReward";
// import AddBayesABArms from "./bayes_ab/addBayesABArms";
// import BayesianABRewardSelection from "./bayes_ab/addPriorReward";
// import AddNotifications from "./addNotifications";


const AllSteps = (exp_type: MethodType): Step[] => {
  const steps = [{
    name: "Configure Prior and Outcome for Experiment",
    component: PriorRewardSelection,
  },
  {
    name: "Add Arms",
    component: AddArms,
  },

]
  if (exp_type === "cmab") {
    steps.splice(0, 0, {
      name: "Configure Prior and Reward",
      component: AddContext,
    });
  }
  return steps;
};

// --- MAB types and steps ---

// const MABsteps: Step[] = [
//   {
//     name: "Configure MAB",
//     component: MABPriorRewardSelection,
//   },
//   {
//     name: "Add Arms",
//     component: AddMABArms,
//   },
//   { name: "Notifications", component: AddNotifications },
// ];

// --- CMAB test types and steps ---

// const CMABsteps: Step[] = [
//   {
//     name: "Configure MAB",
//     component: CMABPriorRewardSelection,
//   },
//   {
//     name: "Add Contexts",
//     component: AddCMABContexts,
//   },
//   {
//     name: "Add Arms",
//     component: AddCMABArms,
//   },
//   { name: "Notifications", component: AddNotifications },
// ];

// --- A/B test types and steps ---

// const BayesianABsteps: Step[] = [
//   {
//     name: "Configure Bayesian A/B Test",
//     component: BayesianABRewardSelection,
//   },
//   {
//     name: "Add Arms",
//     component: AddBayesABArms,
//   },
//   { name: "Notifications", component: AddNotifications },
// ];

// --- All steps ---

// const AllSteps = {
//   mab: MABsteps,
//   cmab: CMABsteps,
//   bayes_ab: BayesianABsteps,
// };

export { AllSteps };
