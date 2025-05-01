import { useExperimentStore } from "../../../store/useExperimentStore";
import { useCallback, useState, useEffect } from "react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import type { RewardType, StepComponentProps } from "../../../types";
import { DividerWithTitle } from "@/components/Dividers";

export default function CMABPriorRewardSelection({
  onValidate,
}: StepComponentProps) {
  const { experimentState, updateRewardType } = useExperimentStore();
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

    // Prior type is fixed as "normal" for CMAB, so we don't need to validate it
    if (!experimentState.reward_type) {
      newErrors.reward_type = "Please select a reward type";
      isValid = false;
    }

    return { isValid, newErrors };
  }, [experimentState.reward_type]);

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
          Configure CMAB Parameters
        </h2>
      </div>
      <div className="pt-6 space-y-6" aria-label="CMAB Parameters">
        <DividerWithTitle title="Prior Type" />
        <div className="space-y-4">
          <Label className="text-base">
            Select prior type for the experiment
          </Label>
          <RadioGroup value="normal" disabled className="space-y-4">
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
          </RadioGroup>
          {errors.prior_type ? (
            <p className="text-destructive text-xs mt-1">{errors.prior_type}</p>
          ) : (
            <p className="text-destructive text-xs mt-1">&nbsp;</p>
          )}
        </div>

        <DividerWithTitle title="Outcome Type" />
        <div className="space-y-4">
          <Label className="text-base">
            Select an outcome type for the experiment
          </Label>
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
