import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Notification } from "../types";

type NotificationType = "days_elapsed" | "trials_completed";
const notificationTypes: Record<NotificationType, string> = {
  days_elapsed: "Days Elapsed",
  trials_completed: "Trials Completed",
};

export default function NotificationDetails({
  notificationData,
  dateCreated,
  nTrials,
}: {
  notificationData: Notification[];
  dateCreated: string | null;
  nTrials: number | null;
}) {
  const daysSinceDate = (dateString: string | null) => {
    if (!dateString) {
      return 0;
    }

    const date = new Date(dateString);
    const now = new Date();
    const diffTime = now.getTime() - date.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const getValue = (notification: Notification) => {
    if (notification.notification_type === "days_elapsed") {
      return daysSinceDate(dateCreated);
    }
    if (notification.notification_type === "trials_completed") {
      return nTrials || 0;
    }
    throw new Error("Unknown notification type");
  };

  return (
    <Card className="min-h-60">
      <CardHeader>
        <CardTitle className="text-lg">Notifications</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {notificationData.map((notification, index) => (
          <div key={index} className="pb-3">
            <div className="flex justify-between">
              <div className="flex items-center">
                <span className="text-muted-foreground">
                  {
                    notificationTypes[
                      notification.notification_type as NotificationType
                    ]
                  }
                </span>
                {getValue(notification) >= notification.notification_value ? (
                  <Check className="text-green-500 ml-1" />
                ) : null}
              </div>

              <div>
                <span className="text-sm">
                  {getValue(notification)} of {notification.notification_value}
                </span>
              </div>
            </div>

            <div className="mt-2 mb-3">
              <Progress
                value={getValue(notification)}
                className="w-full"
                max={notification.notification_value}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
