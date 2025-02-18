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

export type {
  Step,
  Notification,
  ExperimentStateBase,
  ArmBase,
  StepComponentProps,
  MethodType,
};
