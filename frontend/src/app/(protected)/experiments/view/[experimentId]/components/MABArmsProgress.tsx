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

export default function MABArmsProgress({ armsData }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Experiment Arms</CardTitle>
        <CardDescription>Success percentage for each arm</CardDescription>
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
                  {`${((arm.alpha * 100) / (arm.alpha + arm.beta)).toFixed(
                    1
                  )}%`}
                </span>
              </div>
              <Progress
                value={(arm.alpha * 100) / (arm.alpha + arm.beta)}
                className="h-2"
              />
            </div>
          ))}
        </TooltipProvider>
      </CardContent>
    </Card>
  );
}
