import {
  Field,
  FieldGroup,
  Fieldset,
  Label,
  Description,
} from "@/components/catalyst/fieldset";

import { Radio, RadioField, RadioGroup } from "@/components/catalyst/radio";
import { Input } from "@/components/catalyst/input";
import { Textarea } from "@/components/catalyst/textarea";
import { AllSteps } from "./addExperimentSteps";
import { useExperiment } from "./AddExperimentContext";
import { Heading } from "@/components/catalyst/heading";
import {
  MABExperimentState,
  NewMABArm,
  NewABArm,
  ABExperimentState,
} from "../../types";

type Methods = typeof AllSteps;

export default function AddBasicInfo({
  setMethodType,
}: {
  setMethodType: (method: keyof Methods) => void;
}) {
  const { experimentState, setExperimentState } = useExperiment();
  const defaultMABArms: NewMABArm[] = [
    { name: "", description: "", alpha_prior: 1, beta_prior: 1 },
    { name: "", description: "", alpha_prior: 1, beta_prior: 1 },
  ];
  const defaultABArms: NewABArm[] = [
    { name: "", description: "", mean_prior: 0, stdDev_prior: 1 },
    { name: "", description: "", mean_prior: 0, stdDev_prior: 1 },
  ];
  const methodSelect = (value: keyof Methods) => {
    setMethodType(value);
    setExperimentState((prevState) => {
      if (value === "mab") {
        return {
          ...prevState,
          methodType: "mab",
          arms: defaultMABArms, // Ensure this matches your NewMABArm[] type
        } as MABExperimentState;
      } else {
        return {
          ...prevState,
          methodType: "ab",
          arms: defaultABArms, // Ensure this matches your NewABArm[] type
        } as ABExperimentState;
      }
    });
  };

  return (
    <div>
      <div className="pt-5 flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <Heading>Start a new experiment</Heading>
      </div>
      <Fieldset aria-label="New MAB Experiment" className="pt-6">
        <FieldGroup>
          <Field>
            <Label>Experiment Name</Label>
            <Input
              name="experiment-name"
              placeholder="Give it a name you'll remember"
              value={experimentState.name}
              onChange={(e) =>
                setExperimentState({
                  ...experimentState,
                  name: e.target.value,
                })
              }
            />
          </Field>
          <Field>
            <Label>Description</Label>
            <Textarea
              name="experiment-description"
              placeholder="Why are you running this experiment? What do you wish to test?"
              value={experimentState.description}
              rows={3}
              onChange={(e) =>
                setExperimentState({
                  ...experimentState,
                  description: e.target.value,
                })
              }
            />
          </Field>
        </FieldGroup>

        <RadioGroup
          name="experiment-method"
          value={experimentState.methodType}
          onChange={(value) => methodSelect(value as keyof Methods)}
        >
          <Label>Select experiment type</Label>
          <RadioField>
            <Radio id="mab" value="mab" />
            <Label htmlFor="mab">Multi-armed Bandit</Label>
            <Description>
              A method that automatically converges to the best performing arm.
            </Description>
          </RadioField>
          <RadioField>
            <Radio id="ab-test" value="ab" />
            <Label htmlFor="ab-test">A/B Testing</Label>
            <Description>
              A method that compares two or more variants against each other.
            </Description>
          </RadioField>
        </RadioGroup>
      </Fieldset>
    </div>
  );
}
