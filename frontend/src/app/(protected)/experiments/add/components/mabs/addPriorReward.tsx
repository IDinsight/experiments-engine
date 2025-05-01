import { useExperimentStore } from "../../../store/useExperimentStore";
import { useCallback, useState, useEffect } from "react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import type { PriorType, RewardType, StepComponentProps } from "../../../types";
import { DividerWithTitle } from "@/components/Dividers";

export default function MABPriorRewardSelection({
  onValidate,
}: StepComponentProps) {
  const { experimentState, updatePriorType, updateRewardType } =
    useExperimentStore();
  const [errors, setErrors] = useState({
    prior_type: "",
    reward_type: "",
  });

  const validateForm = useCallback(() => {
    let isValid = true;
    const newErrors = {
      prior_type: "",
      reward_type: "",
    };

    if (!experimentState.prior_type) {
      newErrors.prior_type = "Please select a prior type";
      isValid = false;
    }

    if (!experimentState.reward_type) {
      newErrors.reward_type = "Please select a reward type";
      isValid = false;
    }

    if (
      experimentState.prior_type === "normal" &&
      experimentState.reward_type === "binary"
    ) {
      newErrors.reward_type =
        "Normal prior is not compatible with binary reward";
      isValid = false;
    }
    if (
      experimentState.prior_type === "beta" &&
      experimentState.reward_type === "real-valued"
    ) {
      newErrors.reward_type =
        "Beta prior is not compatible with real-valued reward";
      isValid = false;
    }
    return { isValid, newErrors };
  }, [experimentState.prior_type, experimentState.reward_type]);

  useEffect(() => {
    const { isValid, newErrors } = validateForm();
    if (JSON.stringify(newErrors) !== JSON.stringify(errors)) {
      setErrors(newErrors);
      onValidate({ isValid, errors: newErrors });
    }
  }, [validateForm, onValidate, errors]);

  useEffect(() => {
    const { isValid, newErrors } = validateForm();
    setErrors(newErrors);
    onValidate({ isValid, errors: newErrors });
  }, []);

  return (
    <div>
      <div className="pt-5 flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <h2 className="text-2xl font-semibold tracking-tight">
          Configure MAB Parameters
        </h2>
      </div>
      <div className="pt-6 space-y-6" aria-label="MAB Parameters">
        <DividerWithTitle title="Prior Type" />
        <div className="space-y-4">
          <Label>Select prior type for the experiment</Label>
          <RadioGroup
            value={experimentState.prior_type || ""}
            onValueChange={(value) => updatePriorType(value as PriorType)}
            className="space-y-4"
          >
            <div className="flex items-start space-x-2">
              <RadioGroupItem value="normal" id="normal" />
              <div className="grid gap-1.5 leading-none">
                <Label htmlFor="normal" className="font-medium">
                  Normal
                </Label>
                <p className="text-sm text-muted-foreground">
                  Gaussian distribution; best for real-valued outcomes.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-2">
              <RadioGroupItem value="beta" id="beta" />
              <div className="grid gap-1.5 leading-none">
                <Label htmlFor="beta" className="font-medium">
                  Beta
                </Label>
                <p className="text-sm text-muted-foreground">
                  Beta distribution; best for binary outcomes.
                </p>
              </div>
            </div>
          </RadioGroup>
          {errors.prior_type ? (
            <p className="text-destructive text-xs mt-1">{errors.prior_type}</p>
          ) : (
            <p className="text-destructive text-xs mt-1">&nbsp;</p>
          )}
        </div>

        <DividerWithTitle title="Outcome Type" />
        <div className="space-y-4">
          <Label>Select an outcome type for the experiment</Label>
          <RadioGroup
            value={experimentState.reward_type || ""}
            onValueChange={(value) => updateRewardType(value as RewardType)}
            className="space-y-4"
          >
            <div className="flex items-start space-x-2">
              <RadioGroupItem value="real-valued" id="real-valued" />
              <div className="grid gap-1.5 leading-none">
                <Label htmlFor="real-valued" className="font-medium">
                  Real-valued
                </Label>
                <p className="text-sm text-muted-foreground">
                  E.g. how long someone engaged with your app, how long did
                  onboarding take, etc.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-2">
              <RadioGroupItem value="binary" id="binary" />
              <div className="grid gap-1.5 leading-none">
                <Label htmlFor="binary" className="font-medium">
                  Binary
                </Label>
                <p className="text-sm text-muted-foreground">
                  E.g. whether a user clicked on a button, whether a user
                  converted, etc.
                </p>
              </div>
            </div>
          </RadioGroup>
          {errors.reward_type ? (
            <p className="text-destructive text-xs mt-1">
              {errors.reward_type}
            </p>
          ) : (
            <p className="text-destructive text-xs mt-1">&nbsp;</p>
          )}
        </div>
      </div>
    </div>
  );
}
