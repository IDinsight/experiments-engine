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
import { NewMABArm, StepComponentProps } from "../../../types";
import { PlusIcon } from "@heroicons/react/16/solid";
import { DividerWithTitle } from "@/components/Dividers";
import { TrashIcon } from "@heroicons/react/16/solid";
import { Heading } from "@/components/catalyst/heading";
import { useCallback, useEffect, useState } from "react";

export default function AddMABArms({ onValidate }: StepComponentProps) {
  const { experimentState, setExperimentState } = useExperiment();
  const [errors, setErrors] = useState(
    experimentState.arms.map(() => ({
      name: "",
      description: "",
      alpha: "",
      beta: "",
    })),
  );
  const arms = experimentState.arms as NewMABArm[];
  const defaultArm: NewMABArm = {
    name: "",
    description: "",
    alpha: 1,
    beta: 1,
  };

  const validateForm = useCallback(() => {
    let isValid = true;
    const newErrors = arms.map(() => ({
      name: "",
      description: "",
      alpha: "",
      beta: "",
    }));

    arms.forEach((arm, index) => {
      if (!arm.name.trim()) {
        newErrors[index].name = "Arm name is required";
        isValid = false;
      }

      if (!arm.description.trim()) {
        newErrors[index].description = "Description is required";
        isValid = false;
      }

      if (!arm.alpha) {
        newErrors[index].alpha = "Alpha prior is required";
        isValid = false;
      }

      if (!arm.beta) {
        newErrors[index].beta = "Beta prior is required";
        isValid = false;
      }
    });
    return { isValid, newErrors };
  }, [arms]);

  useEffect(() => {
    const { isValid, newErrors } = validateForm();
    if (JSON.stringify(newErrors) !== JSON.stringify(errors)) {
      console.log("setting errors");
      setErrors(newErrors);
      onValidate({ isValid, errors: newErrors });
    }
  }, [validateForm, onValidate, errors]);

  const typeSafeSetExperimentState = (newState: NewMABArm[]) => {
    if (experimentState.methodType === "mab") {
      setExperimentState({
        ...experimentState,
        arms: newState,
      });
    } else {
      console.error("Method type is not MAB");
      throw new Error("Method type is not MAB");
    }
  };

  return (
    <div>
      <div className="flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <Heading>Add MAB Arms</Heading>
        <div className="flex gap-4">
          <Button
            className="mt-4"
            onClick={() =>
              setExperimentState((prevState) => {
                if (prevState.methodType === "mab") {
                  return {
                    ...prevState,
                    arms: [...prevState.arms, defaultArm as NewMABArm],
                  };
                } else {
                  console.error("Method type is not MAB");
                  throw new Error("Method type is not MAB");
                }
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
            onClick={() => {
              if (experimentState.methodType === "mab") {
                setExperimentState({
                  ...experimentState,
                  arms: experimentState.arms.slice(
                    0,
                    experimentState.arms.length - 1,
                  ) as NewMABArm[],
                });
              } else {
                console.error("Method type is not MAB");
                throw new Error("Method type is not MAB");
              }
            }}
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
                <Field className="flex flex-col mb-4">
                  <div className="flex flex-row">
                    <Label className="basis-1/4 mt-3 font-medium">Name</Label>
                    <div className="basis-3/4 flex flex-col">
                      <Input
                        name={`arm-${index + 1}-name`}
                        placeholder="Give the arm a searchable name"
                        value={arm.name || ""}
                        onChange={(e) => {
                          const newArms = [...arms];
                          newArms[index].name = e.target.value;
                          typeSafeSetExperimentState(newArms);
                        }}
                      />
                      {errors[index]?.name ? (
                        <p className="text-red-500 text-xs mt-1">
                          {errors[index].name}
                        </p>
                      ) : (
                        <p className="text-red-500 text-xs mt-1">&nbsp;</p>
                      )}
                    </div>
                  </div>
                </Field>
                <Field className="flex flex-col">
                  <div className="flex flex-row">
                    <Label className="basis-1/4 mt-3 font-medium">
                      Description
                    </Label>
                    <div className="basis-3/4 flex flex-col">
                      <Textarea
                        name={`arm-${index + 1}-description`}
                        placeholder="Describe the arm"
                        value={arm.description || ""}
                        onChange={(e) => {
                          const newArms = [...arms];
                          newArms[index].description = e.target.value;
                          typeSafeSetExperimentState(newArms);
                        }}
                      />
                      {errors[index]?.description ? (
                        <p className="text-red-500 text-xs mt-1">
                          {errors[index].description}
                        </p>
                      ) : (
                        <p className="text-red-500 text-xs mt-1">&nbsp;</p>
                      )}
                    </div>
                  </div>
                </Field>
              </div>
              <div className="basis-1/2 grow">
                <Field className="flex flex-col mb-4">
                  <div className="flex flex-row">
                    <Label className="basis-1/4 mt-3 font-medium">
                      Alpha prior
                    </Label>
                    <div className="basis-3/4 flex flex-col">
                      <Input
                        name={`arm-${index + 1}-alpha`}
                        placeholder="Enter an integer as the prior for the alpha parameter"
                        value={arm.alpha || ""}
                        onChange={(e) => {
                          const newArms = [...arms];
                          newArms[index].alpha = parseInt(e.target.value);
                          typeSafeSetExperimentState(newArms);
                        }}
                      />
                      {errors[index]?.alpha ? (
                        <p className="text-red-500 text-xs mt-1">
                          {errors[index].alpha}
                        </p>
                      ) : (
                        <p className="text-red-500 text-xs mt-1">&nbsp;</p>
                      )}
                    </div>
                  </div>
                </Field>
                <Field className="flex flex-col">
                  <div className="flex flex-row">
                    <Label className="basis-1/4 mt-3 font-medium">
                      Beta prior
                    </Label>
                    <div className="basis-3/4 flex flex-col">
                      <Input
                        name={`arm-${index + 1}-beta`}
                        placeholder="Enter an integer as the prior for the beta parameter"
                        value={arm.beta || ""}
                        onChange={(e) => {
                          const newArms = [...arms];
                          newArms[index].beta = parseInt(e.target.value);
                          typeSafeSetExperimentState(newArms);
                        }}
                      />
                      {errors[index]?.beta ? (
                        <p className="text-red-500 text-xs mt-1">
                          {errors[index].beta}
                        </p>
                      ) : (
                        <p className="text-red-500 text-xs mt-1">&nbsp;</p>
                      )}
                    </div>
                  </div>
                </Field>
              </div>
            </FieldGroup>
          </div>
        ))}
      </Fieldset>
    </div>
  );
}
