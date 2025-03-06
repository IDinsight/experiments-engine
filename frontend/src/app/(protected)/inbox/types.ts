interface Message {
  message_id: number;
  title: string;
  text: string;
  is_unread: boolean;
  created_datetime_utc: string;
}

export type { Message };
