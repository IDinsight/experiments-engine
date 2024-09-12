interface Arm {
  arm_id?: number;
  name: string;
  description: string;
  alpha_prior: number;
  beta_prior: number;
}

interface MAB {
  experiment_id?: number;
  name: string;
  description: string;
  arms: Arm[];
}

export type { Arm, MAB };
