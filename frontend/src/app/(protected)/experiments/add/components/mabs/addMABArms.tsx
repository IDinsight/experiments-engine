import {
  Field,
  FieldGroup,
  Fieldset,
  Label,
} from "@/components/catalyst/fieldset";
import { Button } from "@/components/catalyst/button";
import { Input } from "@/components/catalyst/input";
import { Textarea } from "@/components/catalyst/textarea";
import { useExperiment } from "../AddExperimentContext";
import { NewMABArm } from "../../../types";
import { PlusIcon } from "@heroicons/react/16/solid";
import { DividerWithTitle } from "@/components/Dividers";
import { TrashIcon } from "@heroicons/react/16/solid";
import { Heading } from "@/components/catalyst/heading";
export default function AddMABArms() {
  const { experimentState, setExperimentState } = useExperiment();

  const arms = experimentState.arms as NewMABArm[];
  const defaultArm: NewMABArm = {
    name: "",
    description: "",
    alpha_prior: 1,
    beta_prior: 1,
  };

  return (
    <div>
      <div className="flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <Heading>Add MAB Arms</Heading>
        <div className="flex gap-4">
          <Button
            className="mt-4"
            onClick={() =>
              setExperimentState({
                ...experimentState,
                arms: [...arms, defaultArm],
              })
            }
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Add Arm
          </Button>
          <Button
            className="mt-4 mx-4"
            disabled={arms.length <= 2}
            outline
            onClick={() =>
              arms.length > 2 &&
              setExperimentState({
                ...experimentState,
                arms: arms.slice(0, arms.length - 1),
              })
            }
          >
            <TrashIcon className="w-4 h-4 mr-2" />
            Delete Arm
          </Button>
        </div>
      </div>
      <Fieldset aria-label="Add MAB Arms">
        {arms.map((arm, index) => (
          <div key={index}>
            <DividerWithTitle title={`Arm ${index + 1}`} />
            <FieldGroup
              key={index}
              className="md:flex md:flex-row md:space-x-8 md:space-y-0 items-start"
            >
              <div className="basis-1/2">
                <Field className="flex flex-row ">
                  <Label className="basis-1/4 mt-3">Name</Label>
                  <Input
                    className="basis-3/4"
                    name={`arm-${index + 1}`}
                    placeholder="Give the arm a searchable name"
                    defaultValue={arm.name}
                    onChange={(e) => {
                      const newArms = [...arms];
                      newArms[index].name = e.target.value;
                      setExperimentState({
                        ...experimentState,
                        arms: newArms,
                      });
                    }}
                  />
                </Field>
                <Field className="flex flex-row ">
                  <Label className="basis-1/4 mt-3">Description</Label>
                  <Textarea
                    className="basis-3/4 "
                    name={`arm-${index + 1}-description`}
                    placeholder="What is the hypothesis being tested?"
                    defaultValue={arm.description}
                    rows={3}
                    onChange={(e) => {
                      const newArms = [...arms];
                      newArms[index].description = e.target.value;
                      setExperimentState({
                        ...experimentState,
                        arms: newArms,
                      });
                    }}
                  />
                </Field>
              </div>
              <div className="bases-1/2 grow">
                <Field className="flex flex-row ">
                  <Label className="basis-1/4 mt-3">Alpha prior</Label>
                  <Input
                    className="basis-3/4"
                    name={`arm-${index + 1}-alpha`}
                    placeholder="Enter an integer as the prior for the alpha parameter"
                    defaultValue={arm.alpha_prior}
                    onChange={(e) => {
                      const newArms = [...arms];
                      newArms[index].alpha_prior = parseInt(e.target.value);
                      setExperimentState({
                        ...experimentState,
                        arms: newArms,
                      });
                    }}
                  />
                </Field>
                <Field className="flex flex-row ">
                  <Label className="basis-1/4 mt-3">Beta prior</Label>
                  <Input
                    className="basis-3/4"
                    name={`arm-${index + 1}-beta`}
                    placeholder="Enter an integer as the prior for the beta parameter"
                    defaultValue={arm.beta_prior}
                    onChange={(e) => {
                      const newArms = [...arms];
                      newArms[index].beta_prior = parseInt(e.target.value);
                      setExperimentState({
                        ...experimentState,
                        arms: newArms,
                      });
                    }}
                  />
                </Field>
              </div>
            </FieldGroup>
          </div>
        ))}
      </Fieldset>
    </div>
  );
}
