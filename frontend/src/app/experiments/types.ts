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
  is_active: boolean;
  arms: Arm[];
}

interface BetaParams {
  name: string;
  alpha: number;
  beta: number;
}

export type { Arm, MAB, NewArm, NewMAB, BetaParams };
