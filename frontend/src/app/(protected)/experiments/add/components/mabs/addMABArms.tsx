import {
  useExperimentStore,
  isMABExperimentStateNormal,
} from "../../../store/useExperimentStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import type {
  NewMABArmNormal,
  NewMABArmBeta,
  StepComponentProps,
  // MABArmBeta,
  // MABArmNormal,
} from "../../../types";
import { Plus, Trash } from "lucide-react";
import { DividerWithTitle } from "@/components/Dividers";
import { useCallback, useEffect, useState, useMemo } from "react";

export default function AddMABArms({ onValidate }: StepComponentProps) {
  const { experimentState, updateArm, addArm, removeArm } =
    useExperimentStore();

  const [inputValues, setInputValues] = useState<Record<string, string>>({});

  const baseArmDesc = useMemo(
    () => ({
      name: "",
      description: "",
    }),
    []
  );

  const additionalArmErrors = useMemo(
    () =>
      experimentState.prior_type === "beta"
        ? { alpha_init: "", beta_init: "" }
        : { mu_init: "", sigma_init: "" },
    [experimentState]
  );

  const [errors, setErrors] = useState(() => {
    return experimentState.arms.map(() => {
      return { ...baseArmDesc, ...additionalArmErrors };
    });
  });

  const validateForm = useCallback(() => {
    let isValid = true;
    const newErrors = experimentState.arms.map(() => ({
      ...baseArmDesc,
      ...additionalArmErrors,
    }));

    experimentState.arms.forEach((arm, index) => {
      if (!arm.name.trim()) {
        newErrors[index].name = "Arm name is required";
        isValid = false;
      }

      if (!arm.description.trim()) {
        newErrors[index].description = "Description is required";
        isValid = false;
      }

      if (experimentState.prior_type === "beta") {
        if ("alpha_init" in arm) {
          if (!arm.alpha_init) {
            newErrors[index].alpha_init = "Alpha prior is required";
            isValid = false;
          }
          if (arm.alpha_init <= 0) {
            newErrors[index].alpha_init =
              "Alpha prior should be greater than 0";
            isValid = false;
          }
        }

        if ("beta_init" in arm) {
          if (!arm.beta_init) {
            newErrors[index].beta_init = "Beta prior is required";
            isValid = false;
          }

          if (arm.beta_init <= 0) {
            newErrors[index].beta_init = "Beta prior should be greater than 0";
            isValid = false;
          }
        }
      } else if (experimentState.prior_type === "normal") {
        if ("mu_init" in arm && typeof arm.mu_init !== "number") {
          newErrors[index].mu_init = "Mean value is required";
          isValid = false;
        }

        if ("sigma_init" in arm) {
          if (!arm.sigma_init) {
            newErrors[index].sigma_init = "Std. deviation is required";
            isValid = false;
          }

          if (arm.sigma_init <= 0) {
            newErrors[index].sigma_init =
              "Std deviation should be greater than 0";
            isValid = false;
          }
        }
      }
    });
    return { isValid, newErrors };
  }, [experimentState, baseArmDesc, additionalArmErrors]);

  useEffect(() => {
    const { isValid, newErrors } = validateForm();
    if (JSON.stringify(newErrors) !== JSON.stringify(errors)) {
      setErrors(newErrors);
      onValidate({
        isValid,
        errors: newErrors.map((error) =>
          Object.fromEntries(
            Object.entries(error).map(([key, value]) => [key, value ?? ""])
          )
        ),
      });
    }
  }, [validateForm, onValidate, errors]);

  useEffect(() => {
    const newInputValues: Record<string, string> = {};

    if (isMABExperimentStateNormal(experimentState)) {
      experimentState.arms.forEach((arm, index) => {
        newInputValues[`${index}-mu`] = (
          (arm as NewMABArmNormal).mu_init || 0
        ).toString();
      });
    }
    setInputValues(newInputValues);
  }, [experimentState]);

  const handleNumericChange = (index: number, value: string) => {
    // Update the local input state for a smooth typing experience
    setInputValues((prev) => ({
      ...prev,
      [`${index}-mu`]: value,
    }));

    if (value !== "" && value !== "-") {
      const numValue = Number.parseFloat(value);
      if (!isNaN(numValue)) {
        updateArm(index, { mu_init: numValue });
      }
    }
  };

  return (
    <div>
      <div className="flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <h2 className="text-2xl font-semibold tracking-tight">Add MAB Arms</h2>
        <div className="flex gap-4">
          <Button className="mt-4" onClick={addArm}>
            <Plus className="w-4 h-4 mr-2" />
            Add Arm
          </Button>
          <Button
            className="mt-4 mx-4"
            disabled={experimentState.arms.length <= 2}
            variant="outline"
            onClick={() => {
              removeArm(experimentState.arms.length - 1);
            }}
          >
            <Trash className="w-4 h-4 mr-2" />
            Delete Arm
          </Button>
        </div>
      </div>
      <div className="space-y-6" aria-label="Add MAB Arms">
        {experimentState.arms.map((arm, index) => (
          <div key={index}>
            <DividerWithTitle title={`Arm ${index + 1}`} />
            <div className="md:flex md:flex-row md:space-x-8 md:space-y-0 items-start">
              <div className="basis-1/2">
                <div className="flex flex-col mb-4">
                  <div className="flex flex-row items-start">
                    <Label
                      className="basis-1/4 mt-2 font-medium"
                      htmlFor={`arm-${index + 1}-name`}
                    >
                      Name
                    </Label>
                    <div className="basis-3/4 flex flex-col">
                      <Input
                        id={`arm-${index + 1}-name`}
                        name={`arm-${index + 1}-name`}
                        placeholder="Give the arm a searchable name"
                        value={arm.name || ""}
                        onChange={(e) =>
                          updateArm(index, { name: e.target.value })
                        }
                      />
                      {errors[index]?.name ? (
                        <p className="text-destructive text-xs mt-1">
                          {errors[index].name}
                        </p>
                      ) : (
                        <p className="text-destructive text-xs mt-1">&nbsp;</p>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex flex-col">
                  <div className="flex flex-row items-start">
                    <Label
                      className="basis-1/4 mt-2 font-medium"
                      htmlFor={`arm-${index + 1}-description`}
                    >
                      Description
                    </Label>
                    <div className="basis-3/4 flex flex-col">
                      <Textarea
                        id={`arm-${index + 1}-description`}
                        name={`arm-${index + 1}-description`}
                        placeholder="Describe the arm"
                        value={arm.description || ""}
                        onChange={(e) =>
                          updateArm(index, { description: e.target.value })
                        }
                      />
                      {errors[index]?.description ? (
                        <p className="text-destructive text-xs mt-1">
                          {errors[index].description}
                        </p>
                      ) : (
                        <p className="text-destructive text-xs mt-1">&nbsp;</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              {experimentState.prior_type === "beta" && (
                <div className="basis-1/2 grow">
                  <div className="flex flex-col mb-4">
                    <div className="flex flex-row items-start">
                      <Label
                        className="basis-1/4 mt-2 font-medium"
                        htmlFor={`arm-${index + 1}-alpha`}
                      >
                        Alpha prior
                      </Label>
                      <div className="basis-3/4 flex flex-col">
                        <Input
                          id={`arm-${index + 1}-alpha`}
                          name={`arm-${index + 1}-alpha`}
                          placeholder="Enter an integer as the prior for the alpha parameter"
                          value={(arm as NewMABArmBeta).alpha_init || ""}
                          onChange={(e) => {
                            updateArm(index, {
                              alpha_init: parseInt(e.target.value),
                            });
                          }}
                        />
                        {errors[index]?.alpha_init ? (
                          <p className="text-destructive text-xs mt-1">
                            {errors[index].alpha_init}
                          </p>
                        ) : (
                          <p className="text-destructive text-xs mt-1">
                            &nbsp;
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <div className="flex flex-row items-start">
                      <Label
                        className="basis-1/4 mt-2 font-medium"
                        htmlFor={`arm-${index + 1}-beta`}
                      >
                        Beta prior
                      </Label>
                      <div className="basis-3/4 flex flex-col">
                        <Input
                          id={`arm-${index + 1}-beta`}
                          name={`arm-${index + 1}-beta`}
                          placeholder="Enter an integer as the prior for the beta parameter"
                          value={(arm as NewMABArmBeta).beta_init || ""}
                          onChange={(e) => {
                            updateArm(index, {
                              beta_init: parseInt(e.target.value),
                            });
                          }}
                        />
                        {errors[index]?.beta_init ? (
                          <p className="text-destructive text-xs mt-1">
                            {errors[index].beta_init}
                          </p>
                        ) : (
                          <p className="text-destructive text-xs mt-1">
                            &nbsp;
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              {experimentState.prior_type === "normal" && (
                <div className="basis-1/2 grow">
                  <div className="flex flex-col mb-4">
                    <div className="flex flex-row items-start">
                      <Label
                        className="basis-1/4 mt-2 font-medium"
                        htmlFor={`arm-${index + 1}-mu`}
                      >
                        Mean prior
                      </Label>
                      <div className="basis-3/4 flex flex-col">
                        <Input
                          id={`arm-${index + 1}-mu`}
                          name={`arm-${index + 1}-mu`}
                          type="number"
                          placeholder="Enter a float as mean for the prior"
                          defaultValue={0}
                          value={
                            inputValues[`${index}-mu`] ??
                            (arm as NewMABArmNormal).mu_init?.toString()
                          }
                          onChange={(e) => {
                            handleNumericChange(index, e.target.value);
                          }}
                        />
                        {errors[index]?.mu_init ? (
                          <p className="text-destructive text-xs mt-1">
                            {errors[index].mu_init}
                          </p>
                        ) : (
                          <p className="text-destructive text-xs mt-1">
                            &nbsp;
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <div className="flex flex-row items-start">
                      <Label
                        className="basis-1/4 mt-2 font-medium"
                        htmlFor={`arm-${index + 1}-sigma`}
                      >
                        Standard deviation
                      </Label>
                      <div className="basis-3/4 flex flex-col">
                        <Input
                          id={`arm-${index + 1}-sigma`}
                          name={`arm-${index + 1}-sigma`}
                          type="number"
                          defaultValue={1}
                          placeholder="Enter a float as standard deviation for the prior"
                          value={(arm as NewMABArmNormal).sigma_init || ""}
                          onChange={(e) => {
                            updateArm(index, {
                              sigma_init: Number(e.target.value),
                            });
                          }}
                        />
                        {errors[index]?.sigma_init ? (
                          <p className="text-destructive text-xs mt-1">
                            {errors[index].sigma_init}
                          </p>
                        ) : (
                          <p className="text-destructive text-xs mt-1">
                            &nbsp;
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
