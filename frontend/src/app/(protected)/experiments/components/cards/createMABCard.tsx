import { MABBeta, MABNormal, MABArmBeta, MABArmNormal } from "../../types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useRouter } from "next/navigation";

const calculateDaysAgo = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
};

interface ExperimentCardProps<T> {
  experiment: {
    experiment_id: number | string;
    name: string;
    is_active: boolean;
    last_trial_datetime_utc?: string;
    arms: T[];
  };
  calculateProgressValue: (arm: T, maxValue?: number) => number;
  formatDisplayValue: (arm: T) => string;
  maxValue?: number;
}

export function ExperimentCard<T extends { name: string }>({
  experiment,
  calculateProgressValue,
  formatDisplayValue,
  maxValue,
}: ExperimentCardProps<T>) {
  const { experiment_id, name, is_active, arms } = experiment;
  const router = useRouter();

  return (
    <div className="flex items-center justify-center">
      <Card
        className="cursor-pointer z-60 w-full max-w-[800px] dark:bg-black
                  dark:border-zinc-400 border-zinc-800 dark:shadown-zinc-600"
        onClick={() => {
          router.push(`/experiments/${experiment_id}`);
        }}
      >
        <CardHeader className="flex flex-row items-start align-top justify-between space-y-0 pb-2">
          <div className="flex flex-col space-y-1">
            <CardTitle className="text-2xl font-bold">{name}</CardTitle>
            <CardDescription className="text-sm font-medium text-zinc-400 tracking-wider">
              ID: {experiment_id}
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2 pt-1">
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
          <div className="mt-4">
            <div className="space-y-2">
              {arms &&
                arms.map((arm, index) => (
                  <div key={index} className="flex items-center">
                    <div className="w-36 mr-2 text-sm truncate">{arm.name}</div>
                    <Progress value={calculateProgressValue(arm, maxValue)} />
                    <div className="ml-2 w-12 text-right text-sm">
                      {formatDisplayValue(arm)}
                    </div>
                  </div>
                ))}
            </div>
            <div className="flex flex-row items-center mt-6">
              <span className="uppercase text-xs dark:text-neutral-400 font-medium">
                Last Run:
              </span>
              <span className="text-xs font-medium text-zinc-400 ml-2">
                {experiment.last_trial_datetime_utc
                  ? `${calculateDaysAgo(
                      experiment.last_trial_datetime_utc
                    )} days ago`
                  : "N/A"}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function MABBetaCards({ experiment }: { experiment: MABBeta }) {
  return (
    <ExperimentCard
      experiment={experiment}
      calculateProgressValue={(arm: MABArmBeta) =>
        (arm.alpha * 100) / (arm.alpha + arm.beta)
      }
      formatDisplayValue={(arm: MABArmBeta) =>
        `${((arm.alpha * 100) / (arm.alpha + arm.beta)).toFixed(1)}%`
      }
    />
  );
}

export function MABNormalCards({ experiment }: { experiment: MABNormal }) {
  const maxValue = Math.max(...experiment.arms.map((arm) => arm.mu), 0);
  return (
    <ExperimentCard
      experiment={experiment}
      calculateProgressValue={(arm: MABArmNormal, maxValue) =>
        maxValue ? (arm.mu * 100) / (maxValue * 1.5) : 0
      }
      formatDisplayValue={(arm: MABArmNormal) => `${arm.mu.toFixed(1)}`}
      maxValue={maxValue}
    />
  );
}
