interface NewArm {
  name: string;
  description: string;
  alpha_prior: number;
  beta_prior: number;
}

interface Arm extends NewArm {
  arm_id: number;
  successes: number;
  failures: number;
}

interface NewMAB {
  name: string;
  description: string;
  arms: NewArm[];
}

interface MAB extends NewMAB {
  experiment_id: number;
  isActive: boolean;
  arms: Arm[];
}

export type { Arm, MAB };
