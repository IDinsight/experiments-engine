import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExtraInfo as ExtraInfoType } from "../types";

function formatDate(dateString: string, showTime = false): string {
  if (dateString === null || dateString === undefined) {
    return "N/A";
  }
  const date = new Date(dateString);

  const datePart = date.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  if (showTime) {
    const timePart = date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });

    return `${datePart} at ${timePart}`;
  } else {
    return datePart;
  }
}

export default function ExtraInfo({ data }: { data: ExtraInfoType | null }) {
  if (!data) {
    return <div>No data available</div>;
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Other Info</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1">
          <span className="text-sm text-muted-foreground">1. Last Sample</span>
          <p className="font-medium">{formatDate(data.lastTrialDate, true)}</p>
        </div>

        <div className="space-y-1">
          <span className="text-sm text-muted-foreground">2. Date Created</span>
          <p className="font-medium">{formatDate(data.dateCreated)}</p>
        </div>

        <div className="space-y-1">
          <span className="text-sm text-muted-foreground">3. Date Updated</span>
          <p className="font-medium">{formatDate(data.dateCreated)}</p>
        </div>

        <div className="space-y-1">
          <span className="text-sm text-muted-foreground">
            4. Type of Experiment
          </span>
          <p className="font-medium">{data.experimentType}</p>
        </div>
      </CardContent>
    </Card>
  );
}
