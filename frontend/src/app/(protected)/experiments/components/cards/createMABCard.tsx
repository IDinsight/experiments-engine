import { MABBeta, BetaParams, MABNormal, GaussianParams } from "../../types";
import { motion, AnimatePresence } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { BetaLineChart, NormalLineChart } from "../Charts";
import { useRouter } from "next/navigation";

export function MABBetaCards({
  experiment,
  successes,
  failures,
}: {
  experiment: MABBeta;
  successes: number[];
  failures: number[];
}) {
  const { experiment_id, name, is_active, arms } = { ...experiment };
  const maxValue = Math.max(
    ...arms.map((d, index) => successes[index] + failures[index])
  );

  const router = useRouter();
  return (
    <div className="flex items-center justify-center">
      <Card
        className="cursor-pointer z-60 w-full max-w-[800px] dark:bg-black
                  dark:border-zinc-400 border-zinc-800 dark:shadown-zinc-600"
        onClick={() => {
          router.push(`/experiments/view/${experiment_id}`);
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
                arms.map((dist, index) => (
                  <div key={index} className="flex items-center">
                    <div className="w-24 text-sm">{dist.name}</div>
                    <div className="flex-1 h-4 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary"
                        style={{
                          width: `${
                            maxValue > 0
                              ? (successes[index] / maxValue) * 100
                              : 0
                          }%`,
                        }}
                      />
                    </div>
                    <div className="w-12 text-right text-sm">
                      {successes[index]}%
                    </div>
                  </div>
                ))}
            </div>
            <div className="flex flex-row justify-between mt-4">
              <div className="uppercase text-xs dark:text-neutral-400 font-medium mt-4">
                Last Run: 2 days ago
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function MABNormalCards({
  experiment,
  mu_final, // TODO: this will not work once experiments updates the mu param
  sigma_final, // TODO: this will not work once experiments updates the mu param
}: {
  experiment: MABNormal;
  mu_final: number[];
  sigma_final: number[];
}) {
  const { experiment_id, name, is_active, arms } = { ...experiment };
  const toggleExpand = () => setIsExpanded(!isExpanded);

  const priors: GaussianParams[] = arms.map((arm) => ({
    name: arm.name,
    mu: arm.mu,
    sigma: arm.sigma,
  }));

  const posteriors: GaussianParams[] = arms.map((arm, index) => ({
    name: arm.name,
    mu: mu_final[index],
    sigma: sigma_final[index],
  }));

  return (
    <div className="flex items-center justify-center">
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
          />
        )}
      </AnimatePresence>

      <motion.div
        layout
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 30,
        }}
        className={`${
          isExpanded
            ? "fixed flex inset-0 justify-center items-center col-span-3 z-50"
            : "w-full max-w-md"
        }`}
        onClick={() => {
          toggleExpand();
        }}
      >
        <Card
          className={`${
            isExpanded ? null : "cursor-pointer"
          } z-60 w-full max-w-[800px] dark:bg-black
                      dark:border-zinc-400 border-zinc-800 dark:shadown-zinc-600`}
          onClick={(e) => {
            e.stopPropagation();
            e.nativeEvent.stopImmediatePropagation();
            isExpanded ? null : toggleExpand();
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
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="min-h-100 flex flex-col space-y-4"
              >
                <p className="mt-4 text-base font-light text-neutral-400">
                  {experiment.description}
                </p>
                <div
                  className="flex items-center justify-center rounded align-middle grow w-full
                      min-h-[300px] border border-zinc-800"
                >
                  <NormalLineChart priors={priors} posteriors={posteriors} />
                </div>
              </motion.div>
            )}
            <div className="mt-4">
              <div className="space-y-2">
                {!isExpanded &&
                  arms &&
                  arms.map((dist, index) => (
                    <div key={index} className="flex items-center">
                      <div className="w-24 text-sm">{dist.name}</div>
                      <div className="flex-1 h-4 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary"
                          //   style={{
                          //    width: `${maxValue > 0 ? (successes[index] / maxValue) * 100 : 0}%`,
                          //   }}
                        />
                      </div>
                      <div className="w-12 text-right text-sm">
                        {/* {successes[index]}% */}
                      </div>
                    </div>
                  ))}
              </div>
              <div className="flex flex-row justify-between mt-4">
                <div className="uppercase text-xs dark:text-neutral-400 font-medium mt-4">
                  Last Run: 2 days ago
                </div>
                {isExpanded && (
                  <div className="uppercase text-xs dark:text-neutral-400 font-medium mt-4">
                    No. of samples: 100
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
