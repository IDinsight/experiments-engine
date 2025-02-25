import { useExperiment } from "./AddExperimentContext";
import { Heading } from "@/components/catalyst/heading";
import {
  Checkbox,
  CheckboxField,
  CheckboxGroup,
} from "@/components/catalyst/checkbox";
import { Description, Fieldset, Label } from "@/components/catalyst/fieldset";
import { Input } from "@/components/ui/input";
import { Notifications, StepComponentProps } from "../../types";
import { useCallback, useEffect, useState } from "react";

export default function AddNotifications({ onValidate }: StepComponentProps) {
  const { experimentState, setExperimentState } = useExperiment();
  const notifications = experimentState.notifications;

  const inputClasses = `
    w-16 mx-1 px-1 py-0 h-6 inline-block font-bold rounded-none
    border-0 border-b-4 border-zinc-200 text-center
    focus:border-primary focus:border-0 focus:border-b-2 focus:ring-0 focus:ring-offset-0
    shadow-none appearance-none [&::-webkit-outer-spin-button]:appearance-none
    [&::-webkit-inner-spin-button]:appearance-none
    [-moz-appearance:textfield]
  `;

  const updateNotificationState = (data: Notifications) => {
    const newNotification = { ...notifications, ...data };
    setExperimentState({
      ...experimentState,
      notifications: newNotification,
    });
  };

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
      notifications.onTrialCompletion &&
      (!notifications.numberOfTrials || notifications.numberOfTrials < 0)
    ) {
      newErrors.numberOfTrials = "Number of trials should be greater than 0";
      isValid = false;
    }
    if (
      notifications.onDaysElapsed &&
      (!notifications.daysElapsed || notifications.daysElapsed < 0)
    ) {
      newErrors.daysElapsed = "Days elapsed should be greater than 0";
      isValid = false;
    }
    if (
      notifications.onPercentBetter &&
      (!notifications.percentBetterThreshold ||
        notifications.percentBetterThreshold < 0)
    ) {
      newErrors.percentBetterThreshold = "Threshold should be greater than 0";
      isValid = false;
    }
    return { isValid, newErrors };
  }, [notifications]);

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
        <Heading>Select notifications</Heading>
      </div>
      <Fieldset aria-label="select notifications" className="pt-6">
        <CheckboxGroup>
          <CheckboxField className="flex flex-row">
            <Checkbox
              name="discoverability"
              defaultChecked={notifications.onTrialCompletion || false}
              onChange={(e) =>
                updateNotificationState({ onTrialCompletion: e })
              }
            />
            <Label>
              After
              <Input
                type="number"
                value={notifications.numberOfTrials}
                onChange={(e) => {
                  updateNotificationState({
                    numberOfTrials: Number(e.target.value),
                  });
                }}
                className={`${inputClasses} ${errors.numberOfTrials ? "border-red-500" : ""}`}
                onClick={(e) => e.stopPropagation()}
              />
              {" trials"}
            </Label>
            <Description>
              {errors.numberOfTrials ? (
                <span className="text-red-500">{errors.numberOfTrials}</span>
              ) : (
                <span>
                  Notify me when <b>{notifications.numberOfTrials}</b> number of
                  trials have been run
                </span>
              )}
            </Description>
          </CheckboxField>
          <CheckboxField>
            <Checkbox
              name="discoverability"
              value="time"
              defaultChecked={notifications.onDaysElapsed || false}
              onChange={(e) => updateNotificationState({ onDaysElapsed: e })}
            />
            <Label>
              After
              <Input
                type="number"
                value={notifications.daysElapsed}
                onChange={(e) =>
                  updateNotificationState({
                    daysElapsed: Number(e.target.value),
                  })
                }
                className={`${inputClasses} ${errors.daysElapsed ? "border-red-500" : ""}`}
                onClick={(e) => e.stopPropagation()}
              />
              {" days"}
            </Label>
            <Description>
              {errors.daysElapsed ? (
                <span className="text-red-500">{errors.daysElapsed}</span>
              ) : (
                <span>
                  Notify me when <b>{notifications.daysElapsed}</b> days have
                  passed since the experiment started
                </span>
              )}
            </Description>
          </CheckboxField>
          <CheckboxField>
            <Checkbox
              name="discoverability"
              value="event"
              defaultChecked={notifications.onPercentBetter || false}
              onChange={(e) => updateNotificationState({ onPercentBetter: e })}
            />
            <Label>
              If an arm is superior by
              <Input
                type="number"
                value={notifications.percentBetterThreshold}
                onChange={(e) =>
                  updateNotificationState({
                    percentBetterThreshold: Number(e.target.value),
                  })
                }
                className={`${inputClasses} ${errors.percentBetterThreshold ? "border-red-500" : ""}`}
                onClick={(e) => e.stopPropagation()}
              />
              {"%"}
            </Label>
            <Description>
              {errors.percentBetterThreshold ? (
                <span className="text-red-500">
                  {errors.percentBetterThreshold}
                </span>
              ) : (
                <span>
                  Notify me if an arm is{" "}
                  <b>{notifications.percentBetterThreshold}</b>% better than the
                  other arms
                </span>
              )}
            </Description>
          </CheckboxField>
        </CheckboxGroup>
      </Fieldset>
    </div>
  );
}
