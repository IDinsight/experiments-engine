import { MethodType, Step } from "../../types";
import PriorRewardSelection  from "./addPriorReward";
import AddContext from "./addContext";
import AddArms from "./addArms";
import AddNotifications from "./addNotifications";


const AllSteps = (exp_type: MethodType): Step[] => {
  const steps = [{
    name: "Configure Prior and Outcome for Experiment",
    component: PriorRewardSelection,
  },
  {
    name: "Add Arms",
    component: AddArms,
  },
  { name: "Notifications",
    component: AddNotifications }

]
  if (exp_type === "cmab") {
    steps.splice(0, 0, {
      name: "Configure Prior and Reward",
      component: AddContext,
    });
  }
  return steps;
};

export { AllSteps };
