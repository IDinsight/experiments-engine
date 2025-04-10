import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Info } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";

import { MABArmDetails } from "../types";

export default function MABArmsProgress({
  armsData,
}: {
  armsData: MABArmDetails[];
}) {
  const maxMu = Math.max(...armsData.map((arm) => arm.mu));
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Experiment Arms</CardTitle>
        <CardDescription>
          {armsData.length
            ? armsData[0].beta
              ? "Success percentage for each arm"
              : "Estimated reward for each arm"
            : "No arms data available"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <TooltipProvider>
          {armsData.map((arm, index) => (
            <div className="space-y-2" key={`arms-id-${index}`}>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{arm.name}</span>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="cursor-help">
                        <Info className="h-4 w-4 text-muted-foreground" />
                      </span>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      <p>{arm.description}</p>
                    </TooltipContent>
                  </Tooltip>
                  <div className="text-xs">{"# of trials: "}</div>
                  <Badge variant="outline">{arm.n_outcomes}</Badge>
                </div>
                <span className="text-sm text-muted-foreground">
                  {arm.beta
                    ? `${((arm.alpha * 100) / (arm.alpha + arm.beta)).toFixed(
                        1
                      )}%`
                    : `${arm.mu.toFixed(1)}`}
                </span>
              </div>
              <Progress
                value={
                  arm.beta
                    ? (arm.alpha * 100) / (arm.alpha + arm.beta)
                    : (arm.mu / (maxMu * 2)) * 100
                }
                className="h-2"
              />
            </div>
          ))}
        </TooltipProvider>
      </CardContent>
    </Card>
  );
}
