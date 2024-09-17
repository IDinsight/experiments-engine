import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MAB } from "../types";

export default function ExperimentCars({ experiment }: { experiment: MAB }) {
  const { experiment_id, name, isActive, arms } = { ...experiment };

  const maxValue =
    arms && arms.length > 0
      ? Math.max(...arms.map((d) => d.successes + d.failures))
      : 0;

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          Experiment ID: {experiment_id}
        </CardTitle>
        <div className="flex items-center space-x-2">
          <div
            className={`w-3 h-3 rounded-full ${
              isActive ? "bg-green-500" : "bg-gray-400"
            }`}
          />
          <span className="text-sm font-medium">
            {isActive ? "Active" : "Not Active"}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{name}</div>
        <div className="mt-4">
          <div className="text-sm font-medium text-muted-foreground mb-2">
            Distributions
          </div>
          <div className="space-y-2">
            {arms &&
              arms.map((dist, index) => (
                <div key={index} className="flex items-center">
                  <div className="w-24 text-sm">{dist.name}</div>
                  <div className="flex-1 h-4 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary"
                      style={{
                        width: `${maxValue > 0 ? (dist.successes / maxValue) * 100 : 0}%`,
                      }}
                    />
                  </div>
                  <div className="w-12 text-right text-sm">
                    {dist.successes}%
                  </div>
                </div>
              ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
