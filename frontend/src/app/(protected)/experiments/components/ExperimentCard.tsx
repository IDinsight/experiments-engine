import {
  Card,
  CardContent,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { MABBeta, MABNormal, CMAB, MethodType } from "../types";
import { MABBetaCards, MABNormalCards } from "./cards/createMABCard";
import { CMABCards } from "./cards/createCMABCard";

export default function ExperimentCards({
  experiment,
  methodType,
}: {
  experiment: MABBeta | MABNormal | CMAB;
  methodType: MethodType;
}) {
  if (methodType === "mab" && experiment.priorType === "beta") {
    const betaExperiment = experiment as MABBeta;
    return <MABBetaCards experiment={betaExperiment} />;
  } else if (methodType === "mab" && experiment.priorType === "normal") {
    const normalExperiment = experiment as MABNormal;
    return <MABNormalCards experiment={normalExperiment} />;
  } else if (methodType === "cmab") {
    const cmabExperiment = experiment as CMAB;
    return <CMABCards experiment={cmabExperiment} />;
  }

  // Default case for other experiment types
  return (
    <Card>
      <CardContent>
        <CardTitle>Unsupported Experiment Type</CardTitle>
        <CardDescription>
          This experiment type is not yet supported.
        </CardDescription>
      </CardContent>
    </Card>
  );
}
