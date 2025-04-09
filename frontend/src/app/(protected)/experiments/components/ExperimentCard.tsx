import {
  Card,
  CardContent,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { MABBeta, MABNormal, CMAB, MethodType } from "../types";
import { useState } from "react";
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
    return (
      <MABBetaCards
        experiment={betaExperiment}
        successes={[3, 1]} // TODO: hardcoding these values for demo purposes; need to fetch from API
        failures={[0, 3]} // TODO: hardcoding these values for demo purposes; need to fetch from API
      />
    );
  } else if (methodType === "mab" && experiment.priorType === "normal") {
    const normalExperiment = experiment as MABNormal;
    return (
      <MABNormalCards
        experiment={normalExperiment}
        mu_final={[2.5, -1.3]} // TODO: hardcoding these values for demo purposes; need to fetch from API
        sigma_final={[1.5, 2.3]} // TODO: hardcoding these values for demo purposes; need to fetch from API
      />
    );
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
