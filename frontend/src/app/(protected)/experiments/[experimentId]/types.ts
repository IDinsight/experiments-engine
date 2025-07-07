interface SingleExperimentDetails {
  name: string;
  description: string;
  reward_type: string;
  prior_type: string;
  exp_type: string;
  is_active: boolean;
  experiment_id: number;
  created_datetime_utc: string;
  last_trial_datetime_utc: string;
  n_trials: number;
  arms: ArmDetails[];
  notifications: Notification[];
}

interface ArmDetails {
  name: string;
  description: string;
  alpha_init?: number;
  beta_init?: number;
  mu_init?: number;
  sigma_init?: number;
  alpha?: number;
  beta?: number;
  mu?: number[];
  covariance?: number[][];
  arm_id: number;
  n_outcomes: number;
}

interface Notification {
  notification_id: number;
  notification_type: string;
  notification_value: number;
  is_active: boolean;
}

interface ExtraInfo {
  dateCreated: string;
  lastTrialDate: string;
  experimentType: string;
  nTrials: number;
}

export type { SingleExperimentDetails, ArmDetails, Notification, ExtraInfo };
