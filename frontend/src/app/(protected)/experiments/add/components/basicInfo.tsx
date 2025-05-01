import { useExperimentStore } from "../../store/useExperimentStore";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState, useEffect, useCallback } from "react";
import type { AllSteps } from "./addExperimentSteps";
import type { StepValidation } from "../../types";
import { MethodCard } from "./methodCard";
import { DividerWithTitle } from "@/components/Dividers";

type Methods = typeof AllSteps;

// Method information with detailed descriptions
const methodInfo = {
  mab: {
    title: "Multi-armed Bandit",
    description:
      "A method that automatically converges to the best performing arm.",
    infoTitle: "About Multi-armed Bandit",
    infoDescription:
      "Multi-armed bandit algorithms balance exploration (trying different options) and exploitation (selecting the best known option). They're ideal for scenarios where you want to maximize rewards while learning which option performs best. The algorithm automatically adjusts allocation to favor better performing options over time, minimizing opportunity cost compared to traditional A/B testing.",
    disabled: false,
  },
  cmab: {
    title: "Contextual Bandit",
    description:
      "A method that automatically converges to the best performing arm conditional on context.",
    infoTitle: "About Contextual Bandit",
    infoDescription:
      "Contextual bandits extend the multi-armed bandit approach by considering contextual information when making decisions. This allows the algorithm to learn which option performs best in specific contexts or for specific user segments. It's particularly useful when different users or situations might respond differently to the same options.",
    disabled: false,
  },
  bayes_ab: {
    title: "Bayesian A/B Testing",
    description:
      "A method that compares two or more variants against each other.",
    infoTitle: "About Bayesian A/B Testing",
    infoDescription:
      "Bayesian A/B testing is a controlled experiment where two or more variants are shown to users at random to determine which performs better according to predefined metrics. Unlike bandit methods, A/B tests typically maintain fixed traffic allocation throughout the experiment duration, and only returns the better performing arm at the end of the experiment.",
    disabled: false,
  },
};

export default function AddBasicInfo({
  onValidate,
}: {
  onValidate: (validation: StepValidation) => void;
}) {
  const {
    experimentState,
    updateName,
    updateDescription,
    updateMethodType,
    updateStickyAssignment,
    updateAutoFail,
    updateAutoFailValue,
    updateAutoFailUnit,
  } = useExperimentStore();

  const [errors, setErrors] = useState({
    name: "",
    description: "",
    methodType: "",
  });

  const validateForm = useCallback(() => {
    let isValid = true;
    const newErrors = { name: "", description: "", methodType: "" };

    if (!experimentState.name.trim()) {
      newErrors.name = "Experiment name is required";
      isValid = false;
    }

    if (!experimentState.description.trim()) {
      newErrors.description = "Description is required";
      isValid = false;
    }

    if (!experimentState.methodType) {
      newErrors.methodType = "Please select an experiment type";
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
      <div className="pt-5 flex w-full flex-wrap items-end justify-between gap-4 border-b pb-6 ">
        <h2 className="text-2xl font-semibold tracking-tight">
          Start a new experiment
        </h2>
      </div>
      <div className="pt-6 space-y-6" aria-label="New MAB Experiment">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="experiment-name">Experiment Name</Label>
            <Input
              id="experiment-name"
              name="experiment-name"
              placeholder="Give it a name you'll remember"
              value={experimentState.name}
              onChange={(e) => {
                updateName(e.target.value);
              }}
            />
            {errors.name ? (
              <p className="text-destructive text-xs mt-1">{errors.name}</p>
            ) : (
              <p className="text-destructive text-xs mt-1">&nbsp;</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="experiment-description">Description</Label>
            <Textarea
              id="experiment-description"
              name="experiment-description"
              placeholder="Why are you running this experiment? What do you wish to test?"
              value={experimentState.description}
              rows={3}
              onChange={(e) => {
                updateDescription(e.target.value);
              }}
            />
            {errors.description ? (
              <p className="text-destructive text-xs mt-1">
                {errors.description}
              </p>
            ) : (
              <p className="text-destructive text-xs mt-1">&nbsp;</p>
            )}
          </div>
        </div>
        <div className="mt-6">
          <Label className="mb-3 font-medium">Select experiment type</Label>
          <div
            className="grid grid-cols-1 md:grid-cols-3 gap-4"
            role="radiogroup"
            aria-required="true"
            aria-label="Experiment type"
          >
            {(Object.keys(methodInfo) as Array<keyof typeof methodInfo>).map(
              (method) => (
                <MethodCard
                  key={method}
                  title={methodInfo[method].title}
                  description={methodInfo[method].description}
                  infoTitle={methodInfo[method].infoTitle}
                  infoDescription={methodInfo[method].infoDescription}
                  selected={experimentState.methodType === method}
                  disabled={methodInfo[method].disabled}
                  onClick={() => updateMethodType(method as keyof Methods)}
                />
              )
            )}
          </div>
          {errors.methodType ? (
            <p className="text-destructive text-xs mt-2">{errors.methodType}</p>
          ) : (
            <p className="text-destructive text-xs mt-2">&nbsp;</p>
          )}
        </div>
        <DividerWithTitle title="Other options" />

        {/* Sticky Assignment Switch */}
        <div className="mt-6 space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5 pr-2">
              <Label htmlFor="sticky-assignment">
                Enable sticky assignment
              </Label>
              <p className="text-sm text-muted-foreground">
                Ensures users consistently see the same variant across sessions
              </p>
            </div>
            <Switch
              id="sticky-assignment"
              checked={experimentState.stickyAssignment}
              onCheckedChange={updateStickyAssignment}
            />
          </div>

          {/* Auto Fail After Switch with Input and Dropdown */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5 pr-2">
                <Label htmlFor="auto-fail">Auto fail after</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically fail the experiment after a specified time
                  period if there has been no outcome recorded.
                </p>
              </div>
              <Switch
                id="auto-fail"
                checked={experimentState.autoFail}
                onCheckedChange={updateAutoFail}
              />
            </div>

            {/* Always reserve space for the input fields */}
            <div className="h-[44px] mt-2">
              {/* Actual input fields with opacity transition */}
              <div
                className="flex flex-wrap items-center gap-3 transition-opacity duration-200 ease-in-out"
                style={{
                  opacity: experimentState.autoFail ? 1 : 0,
                  pointerEvents: experimentState.autoFail ? "auto" : "none",
                  position: "relative",
                  zIndex: experimentState.autoFail ? 1 : -1,
                }}
              >
                <div className="w-24">
                  <Input
                    type="number"
                    value={experimentState.autoFailValue}
                    onChange={(e) => {
                      const numValue = Number.parseInt(e.target.value, 10) || 0;
                      updateAutoFailValue(numValue);
                    }}
                    min="1"
                    aria-hidden={!experimentState.autoFail}
                    tabIndex={experimentState.autoFail ? 0 : -1}
                  />
                </div>
                <div className="w-32 ">
                  <Select
                    value={experimentState.autoFailUnit}
                    onValueChange={updateAutoFailUnit}
                    disabled={!experimentState.autoFail}
                  >
                    <SelectTrigger
                      aria-hidden={!experimentState.autoFail}
                      tabIndex={experimentState.autoFail ? 0 : -1}
                    >
                      <SelectValue placeholder="Select unit" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hours">Hours</SelectItem>
                      <SelectItem value="days">Days</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
