import { useExperimentStore } from "../../store/useExperimentStore";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import type { StepComponentProps } from "../../types";
import { useCallback, useEffect, useState } from "react";

export default function AddNotifications({ onValidate }: StepComponentProps) {
  const { experimentState, updateNotifications } = useExperimentStore();

  const inputClasses = `
    w-16 mx-1 px-1 py-0 h-6 inline-block font-bold rounded-none
    border-0 border-b-4 border-zinc-200 text-center
    focus:border-primary focus:border-0 focus:border-b-2 focus:ring-0 focus:ring-offset-0
    shadow-none appearance-none [&::-webkit-outer-spin-button]:appearance-none
    [&::-webkit-inner-spin-button]:appearance-none
    [-moz-appearance:textfield]
  `;

  const [errors, setErrors] = useState({
    numberOfTrials: "",
    daysElapsed: "",
    percentBetterThreshold: "",
  });

  const validateForm = useCallback(() => {
    let isValid = true;
    const newErrors = {
      numberOfTrials: "",
      daysElapsed: "",
      percentBetterThreshold: "",
    };

    if (
      experimentState.notifications.onTrialCompletion &&
      (!experimentState.notifications.numberOfTrials ||
        experimentState.notifications.numberOfTrials < 0)
    ) {
      newErrors.numberOfTrials = "Number of trials should be greater than 0";
      isValid = false;
    }
    if (
      experimentState.notifications.onDaysElapsed &&
      (!experimentState.notifications.daysElapsed ||
        experimentState.notifications.daysElapsed < 0)
    ) {
      newErrors.daysElapsed = "Days elapsed should be greater than 0";
      isValid = false;
    }
    if (
      experimentState.notifications.onPercentBetter &&
      (!experimentState.notifications.percentBetterThreshold ||
        experimentState.notifications.percentBetterThreshold < 0)
    ) {
      newErrors.percentBetterThreshold = "Threshold should be greater than 0";
      isValid = false;
    }
    return { isValid, newErrors };
  }, [experimentState]);

  useEffect(() => {
    const { isValid, newErrors } = validateForm();
    if (JSON.stringify(newErrors) !== JSON.stringify(errors)) {
      setErrors(newErrors);
      onValidate({ isValid, errors: newErrors });
    }
  }, [validateForm, onValidate, errors]);

  return (
    <div>
      <div className="pt-5 flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <h2 className="text-2xl font-semibold tracking-tight">
          Select notifications
        </h2>
      </div>
      <div className="pt-6 space-y-4" aria-label="select notifications">
        <div className="space-y-6">
          <div className="flex items-start space-x-4">
            <Checkbox
              id="trial-completion"
              className="mt-1"
              checked={experimentState.notifications.onTrialCompletion || false}
              onCheckedChange={(checked) =>
                updateNotifications({
                  ...experimentState.notifications,
                  onTrialCompletion: checked as boolean,
                })
              }
            />
            <div className="grid gap-1.5 leading-none">
              <Label
                htmlFor="trial-completion"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                After
                <Input
                  type="number"
                  value={experimentState.notifications.numberOfTrials}
                  onChange={(e) => {
                    updateNotifications({
                      ...experimentState.notifications,
                      numberOfTrials: Number(e.target.value),
                    });
                  }}
                  className={`${inputClasses} ${
                    errors.numberOfTrials ? "border-red-500" : ""
                  }`}
                  onClick={(e) => e.stopPropagation()}
                />
                {" trials"}
              </Label>
              <p className="text-sm text-muted-foreground">
                {errors.numberOfTrials ? (
                  <span className="text-destructive">
                    {errors.numberOfTrials}
                  </span>
                ) : (
                  <span>
                    Notify me when{" "}
                    <b>{experimentState.notifications.numberOfTrials}</b> number
                    of trials have been run
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4">
            <Checkbox
              id="days-elapsed"
              className="mt-1"
              checked={experimentState.notifications.onDaysElapsed || false}
              onCheckedChange={(checked) =>
                updateNotifications({
                  ...experimentState.notifications,
                  onDaysElapsed: checked as boolean,
                })
              }
            />
            <div className="grid gap-1.5 leading-none">
              <Label
                htmlFor="days-elapsed"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                After
                <Input
                  type="number"
                  value={experimentState.notifications.daysElapsed}
                  onChange={(e) =>
                    updateNotifications({
                      ...experimentState.notifications,
                      daysElapsed: Number(e.target.value),
                    })
                  }
                  className={`${inputClasses} ${
                    errors.daysElapsed ? "border-red-500" : ""
                  }`}
                  onClick={(e) => e.stopPropagation()}
                />
                {" days"}
              </Label>
              <p className="text-sm text-muted-foreground">
                {errors.daysElapsed ? (
                  <span className="text-destructive">{errors.daysElapsed}</span>
                ) : (
                  <span>
                    Notify me when{" "}
                    <b>{experimentState.notifications.daysElapsed}</b> days have
                    passed since the experiment started
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4">
            <Checkbox
              id="percent-better"
              className="mt-1"
              disabled={true}
              checked={experimentState.notifications.onPercentBetter || false}
              onCheckedChange={(checked) =>
                updateNotifications({
                  ...experimentState.notifications,
                  onPercentBetter: checked as boolean,
                })
              }
            />
            <div className="grid gap-1.5 leading-none">
              <Label
                htmlFor="percent-better"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-gray-400"
              >
                [Coming soon] If an arm is superior by
                <Input
                  type="number"
                  value={experimentState.notifications.percentBetterThreshold}
                  onChange={(e) =>
                    updateNotifications({
                      ...experimentState.notifications,
                      percentBetterThreshold: Number(e.target.value),
                    })
                  }
                  className={`${inputClasses} ${
                    errors.percentBetterThreshold ? "border-red-500" : ""
                  }`}
                  onClick={(e) => e.stopPropagation()}
                  disabled={true}
                />
                {"%"}
              </Label>
              <p className="text-sm text-muted-foreground">
                {errors.percentBetterThreshold ? (
                  <span className="text-destructive">
                    {errors.percentBetterThreshold}
                  </span>
                ) : (
                  <span>
                    Notify me if an arm is{" "}
                    <b>
                      {experimentState.notifications.percentBetterThreshold}
                    </b>
                    % better than the other arms
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
