"use client";

import { useState } from "react";
import { Button } from "@/components/catalyst/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Trash, MailOpen, MailIcon } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

interface Notification {
  id: string;
  title: string;
  content: string;
  isRead: boolean;
  timestamp: string;
}

// Mock data for notifications
const initialNotifications: Notification[] = [
  {
    id: "1",
    title: "Experiment X: Number of trials reached",
    content:
      "The experiment has reached the target number of trials. Check out the experiment and results here",
    isRead: false,
    timestamp: "2025-02-12T10:00:00Z",
  },
  {
    id: "2",
    title: "Experiment Y: Arm A1 is at least p% better than other arms",
    content:
      "One of the arms in the experiment is better than the threshold compared to the other arms. Check out the experiment and results here",
    isRead: true,
    timestamp: "2025-02-11T15:30:00Z",
  },
  {
    id: "3",
    title: "Experiment Z: D days since started",
    content:
      "The experiment has been running for D days. Check out the experiment and results here",
    isRead: false,
    timestamp: "2023-05-31T09:00:00Z",
  },
];

export default function NotificationPage() {
  const [notifications, setNotifications] =
    useState<Notification[]>(initialNotifications);
  const [selectedNotificationIds, setSelectedNotificationIds] = useState<
    string[]
  >([]);
  const [selectedNotification, setSelectedNotification] =
    useState<Notification | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleCheckboxChange = (notificationId: string) => {
    setSelectedNotificationIds((prev) =>
      prev.includes(notificationId)
        ? prev.filter((id) => id !== notificationId)
        : [...prev, notificationId],
    );
  };

  const handleNotificationClick = (notification: Notification) => {
    setSelectedNotification(notification);
    setIsDrawerOpen(true);
    if (!notification.isRead) {
      setNotifications(
        notifications.map((n) =>
          n.id === notification.id ? { ...n, isRead: true } : n,
        ),
      );
    }
  };

  const handleDeleteSelected = () => {
    setNotifications(
      notifications.filter((n) => !selectedNotificationIds.includes(n.id)),
    );
    setSelectedNotificationIds([]);
    setSelectedNotification(null);
  };

  const handleToggleReadSelected = (markAsRead: boolean) => {
    setNotifications(
      notifications.map((n) =>
        selectedNotificationIds.includes(n.id)
          ? { ...n, isRead: markAsRead }
          : n,
      ),
    );
    setSelectedNotificationIds([]);
  };

  const getTimestampString = (timestamp: string) => {
    //Format the timestamp to say "today" or "yesterday" if applicable.
    // Always include time.
    const timeDifference = new Date().getTime() - new Date(timestamp).getTime();
    const daysDifference = timeDifference / (1000 * 3600 * 24);
    if (daysDifference < 1) {
      if (new Date(timestamp).getDate() === new Date().getDate()) {
        return `Today, ${new Date(timestamp).toLocaleString(undefined, {
          hour: "2-digit",
          minute: "2-digit",
        })}`;
      } else {
        return `Yesterday, ${new Date(timestamp).toLocaleString(undefined, {
          hour: "2-digit",
          minute: "2-digit",
        })}`;
      }
    } else {
      return new Date(timestamp).toLocaleString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    }
  };

  return (
    <div className="w-full p-4 min-h-screen flex flex-col">
      {/* Action Buttons */}
      <div className="mb-4 flex justify-between gap-2">
        <div className="flex gap-2">
          <Button
            outline
            onClick={() => handleToggleReadSelected(true)}
            disabled={selectedNotificationIds.length === 0}
          >
            <MailIcon size={16} className="mr-2" />
            Read
          </Button>

          <Button
            outline
            onClick={() => handleToggleReadSelected(false)}
            disabled={selectedNotificationIds.length === 0}
          >
            <MailOpen size={16} className="mr-2" />
            Unread
          </Button>
        </div>

        <Button
          onClick={handleDeleteSelected}
          disabled={selectedNotificationIds.length === 0}
        >
          <Trash size={16} className="mr-2" />
          Delete
        </Button>
      </div>

      {/* Notifications List */}
      <ScrollArea className="flex-grow border rounded-md">
        <div className="divide-y">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className={`grid grid-cols-[auto_1fr_auto] gap-4 p-4 cursor-pointer hover:bg-gray-100 ${
                notification.id === selectedNotification?.id
                  ? "bg-gray-100"
                  : ""
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
          ))}
        </div>
      </ScrollArea>

      {/* Notification Detail Drawer */}
      <Sheet open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
        <SheetContent className="w-screen sm:w-[400px]">
          {selectedNotification && (
            <>
              <SheetHeader>
                <SheetTitle>{selectedNotification.title}</SheetTitle>
              </SheetHeader>
              <div className="mt-4">
                <p className="text-sm text-gray-500 mb-4">
                  {new Date(selectedNotification.timestamp).toLocaleString(
                    undefined,
                    {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    },
                  )}
                </p>
                <ScrollArea className="h-[calc(100vh-8rem)]">
                  <p className="text-gray-700">
                    {selectedNotification.content}
                  </p>
                </ScrollArea>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
