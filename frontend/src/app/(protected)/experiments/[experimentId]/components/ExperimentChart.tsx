import { useState } from "react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { SingleExperimentDetails } from "../types";
import { BetaLineChart, NormalLineChart } from "./Charts";

export default function MABChart({
  experimentData,
}: {
  experimentData: SingleExperimentDetails | null;
}) {
  const [showPriors, setShowPriors] = useState(false);

  if (!experimentData) {
    return <div>No data available</div>;
  }

  const priorBetaData = experimentData.arms.map((arm) => ({
    name: arm.name,
    alpha: arm.alpha_init ? arm.alpha_init : 1,
    beta: arm.beta_init ? arm.beta_init : 1,
  }));


  const posteriorBetaData = experimentData.arms.map((arm) => ({
    name: arm.name,
    alpha: arm.alpha ? arm.alpha : 1,
    beta: arm.beta ? arm.beta : 1,
  }));

  const priorGaussianData = experimentData.arms.map((arm) => ({
    name: arm.name,
    mu: [arm.mu_init ? arm.mu_init : 0],
    covariance: [[arm.sigma_init ? arm.sigma_init : 1]],
  }));

  const posteriorGaussianData = experimentData.arms.map((arm) => ({
    name: arm.name,
    mu: arm.mu ? arm.mu : [0],
    covariance: arm.covariance ? arm.covariance : [[1]],
  }));

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-lg">Experiment Results</CardTitle>
            <CardDescription>Plotting performance of each arm</CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <label htmlFor="show-priors" className="text-sm font-medium">
              Show Priors
            </label>
            <Switch
              id="show-priors"
              checked={showPriors}
              onCheckedChange={setShowPriors}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          {experimentData.prior_type == "beta" ? (
            <BetaLineChart posteriors={posteriorBetaData} priors={priorBetaData} showPriors={showPriors} />
          ) : (
            <NormalLineChart posteriors={posteriorGaussianData} priors={priorGaussianData} showPriors={showPriors} />
          )}
        </div>
      </CardContent>
    </Card>
  );
}
