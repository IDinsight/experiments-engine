import React from "react";

interface Notification {
  id: string;
  title: string;
  content: string;
  isRead: boolean;
  timestamp: string;
}

export default function NotificationItem({
  notification,
}: {
  notification: Notification;
}) {
  return (
    <div
      key={notification.id}
      className={`grid grid-cols-[auto_1fr_auto] gap-4 p-4 cursor-pointer hover:bg-gray-100 ${
        notification.id === selectedNotification?.id ? "bg-gray-100" : ""
      }`}
      onClick={() => handleNotificationClick(notification)}
    >
      <div className="pt-1">
        <Checkbox
          checked={selectedNotificationIds.includes(notification.id)}
          onCheckedChange={() => handleCheckboxChange(notification.id)}
          onClick={(e) => e.stopPropagation()}
        />
      </div>
      <div className="min-w-0">
        <div
          className={`${!notification.isRead ? "font-bold" : "font-medium"} truncate`}
        >
          {notification.title}
        </div>
        <p
          className={`${!notification.isRead ? "font-bold" : "font-medium"} text-sm text-gray-600 truncate`}
        >
          {notification.content}
        </p>
      </div>
      <div className="text-xs text-gray-500 w-38 text-right hidden md:block">
        {getTimestampString(notification.timestamp)}
      </div>
    </div>
  );
}
