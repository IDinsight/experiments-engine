import { useExperimentStore } from "../../../store/useExperimentStore";
import { useCallback, useState, useEffect } from "react";
import { Radio, RadioField, RadioGroup } from "@/components/catalyst/radio";
import { Fieldset, Label, Description } from "@/components/catalyst/fieldset";
import { PriorType, RewardType, StepComponentProps } from "../../../types";
import { Heading } from "@/components/catalyst/heading";
import { DividerWithTitle } from "@/components/Dividers";

export default function MABPriorRewardSelection({
  onValidate,
}: StepComponentProps) {
  const { experimentState, updatePriorType, updateRewardType } =
    useExperimentStore();
  const [errors, setErrors] = useState({
    priorType: "",
    rewardType: "",
  });

  const validateForm = useCallback(() => {
    let isValid = true;
    const newErrors = {
      priorType: "",
      rewardType: "",
    };

    if (!experimentState.priorType) {
      newErrors.priorType = "Please select a prior type";
      isValid = false;
    }

    if (!experimentState.rewardType) {
      newErrors.rewardType = "Please select a reward type";
      isValid = false;
    }

    if (
      experimentState.priorType === "normal" &&
      experimentState.rewardType === "binary"
    ) {
      newErrors.rewardType =
        "Normal prior is not compatible with binary reward";
      isValid = false;
    }
    if (
      experimentState.priorType === "beta" &&
      experimentState.rewardType === "real-valued"
    ) {
      newErrors.rewardType =
        "Beta prior is not compatible with real-valued reward";
      isValid = false;
    }
    return { isValid, newErrors };
  }, [experimentState.priorType, experimentState.rewardType]);

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
        <Heading>Configure MAB Parameters</Heading>
      </div>
      <Fieldset aria-label="MAB Parameters" className="pt-6">
        <DividerWithTitle title="Prior Type" />
        <RadioGroup
          name="priorType"
          defaultValue=""
          onChange={(value) => updatePriorType(value as PriorType)}
          value={experimentState.priorType}
        >
          <div className="mb-4" />
          <Label>Select prior type for the experiment</Label>
          <RadioField>
            <Radio id="normal" value="normal" />
            <Label htmlFor="normal">Normal</Label>
            <Description>
              Gaussian distribution; best for real-valued outcomes.
            </Description>
          </RadioField>

          <RadioField>
            <Radio id="beta" value="beta" />
            <Label htmlFor="beta">Beta</Label>
            <Description>
              Beta distribution; best for binary outcomes.
            </Description>
          </RadioField>
        </RadioGroup>
        {errors.priorType ? (
          <p className="text-red-500 text-xs mt-1">{errors.priorType}</p>
        ) : (
          <p className="text-red-500 text-xs mt-1">&nbsp;</p>
        )}

        <DividerWithTitle title="Outcome Type" />
        <RadioGroup
          name="rewardType"
          defaultValue=""
          onChange={(value) => updateRewardType(value as RewardType)}
          value={experimentState.rewardType}
        >
          <div className="mb-4" />
          <Label>Select an outcome type for the experiment</Label>
          <RadioField>
            <Radio id="real-valued" value="real-valued" />
            <Label htmlFor="real-valued">Real-valued</Label>
            <Description>
              E.g. how long someone engaged with your app, how long did
              onboarding take, etc.
            </Description>
          </RadioField>

          <RadioField>
            <Radio id="binary" value="binary" />
            <Label htmlFor="binary">Binary</Label>
            <Description>
              E.g. whether a user clicked on a button, whether a user converted,
              etc.
            </Description>
          </RadioField>
        </RadioGroup>
        {errors.rewardType ? (
          <p className="text-red-500 text-xs mt-1">{errors.rewardType}</p>
        ) : (
          <p className="text-red-500 text-xs mt-1">&nbsp;</p>
        )}
      </Fieldset>
    </div>
  );
}
