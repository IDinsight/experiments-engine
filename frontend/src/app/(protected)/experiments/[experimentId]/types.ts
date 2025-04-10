interface MABExperimentDetails {
  name: string;
  description: string;
  reward: string;
  prior_type: string;
  is_active: boolean;
  experiment_id: number;
  created_datetime_utc: string;
  last_trial_datetime_utc: string;
  n_trials: number;
  arms: MABArmDetails[];
  notifications: Notification[];
}

interface MABArmDetails {
  name: string;
  description: string;
  alpha: number;
  beta: number;
  mu: number;
  sigma: number;
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

export type { MABExperimentDetails, MABArmDetails, Notification, ExtraInfo };
