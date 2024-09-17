import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MAB } from "../types";

export default function ExperimentCars({ experiment }: { experiment: MAB }) {
  const { experiment_id, name, is_active, arms } = { ...experiment };

  const maxValue =
    arms && arms.length > 0
      ? Math.max(...arms.map((d) => d.successes + d.failures))
      : 0;
  return (
    <Card className="w-full h-full max-w-md dark:bg-black dark:border-zinc-400 border-zinc-800 dark:shadown-zinc-600">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-zinc-400 tracking-wider">
          ID: {experiment_id}
        </CardTitle>
        <div className="flex items-center space-x-2">
          <div
            className={`w-3 h-3 rounded-full ${
              is_active ? "bg-green-500" : "bg-gray-400"
            }`}
          />
          <span className="text-sm font-medium">
            {is_active ? "Active" : "Not Active"}
          </span>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col flex-between">
        <div className="text-2xl font-bold">{name ? name : ""}</div>
        <div className="mt-4">
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
          <div className="uppercase text-xs dark:text-neutral-400 font-medium mt-4">
            Last Run: 2 days ago
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
