export interface Workspace {
  workspace_id: number;
  workspace_name: string;
  api_daily_quota: number;
  content_quota: number;
  api_key_first_characters: string;
  api_key_updated_datetime_utc: string;
  api_key_rotated_by_user_id?: number;
  api_key_rotated_by_username?: string;
  created_datetime_utc: string;
  updated_datetime_utc: string;
  is_default: boolean;
}

export interface WorkspaceUser {
  user_id: number;
  username: string;
  first_name: string;
  last_name: string;
  role: string;
  is_default_workspace: boolean;
  created_datetime_utc: string;
}

export interface ApiKeyRotation {
  rotation_id: number;
  workspace_id: number;
  rotated_by_user_id: number;
  rotated_by_username: string;
  key_first_characters: string;
  rotation_datetime_utc: string;
}
