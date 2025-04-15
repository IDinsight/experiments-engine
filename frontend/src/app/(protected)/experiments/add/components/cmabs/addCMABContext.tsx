import {
  Field,
  FieldGroup,
  Fieldset,
  Label,
} from "@/components/catalyst/fieldset";
import { Button } from "@/components/catalyst/button";
import { Input } from "@/components/catalyst/input";
import { Textarea } from "@/components/catalyst/textarea";
import { useExperimentStore } from "../../../store/useExperimentStore";
import {
  CMABExperimentState,
  StepComponentProps,
  ContextType,
} from "../../../types";
import { PlusIcon } from "@heroicons/react/16/solid";
import { DividerWithTitle } from "@/components/Dividers";
import { TrashIcon } from "@heroicons/react/16/solid";
import { Heading } from "@/components/catalyst/heading";
import { useCallback, useEffect, useState } from "react";
import { Radio, RadioGroup, RadioField } from "@/components/catalyst/radio";

export default function AddCMABContext({ onValidate }: StepComponentProps) {
  const { experimentState, updateContext, addContext, removeContext } =
    useExperimentStore();

  const [errors, setErrors] = useState<
    Array<{ name: string; description: string; value_type: string }>
  >([{ name: "", description: "", value_type: "" }]);

  const validateForm = useCallback(() => {
    let isValid = true;
    const newErrors = (experimentState as CMABExperimentState).contexts.map(
      () => ({
        name: "",
        description: "",
        value_type: "",
      })
    );

    (experimentState as CMABExperimentState).contexts.forEach(
      (context, index) => {
        if (!context.name.trim()) {
          newErrors[index].name = "Context name is required";
          isValid = false;
        }

        if (!context.description.trim()) {
          newErrors[index].description = "Description is required";
          isValid = false;
        }

        if (!context.value_type.trim()) {
          newErrors[index].value_type = "Context value type is required";
          isValid = false;
        }
      }
    );

    return { isValid, newErrors };
  }, [experimentState]);

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

  return (
    <div>
      <div className="pt-5 flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <Heading>Add CMAB Contexts</Heading>
        <div className="flex gap-4">
          <Button className="mt-4" onClick={addContext}>
            <PlusIcon className="w-4 h-4 mr-2" />
            Add Context
          </Button>
          <Button
            className="mt-4 mx-4"
            disabled={
              (experimentState as CMABExperimentState).contexts.length <= 1
            }
            outline
            onClick={() =>
              removeContext(
                (experimentState as CMABExperimentState).contexts.length - 1
              )
            }
          >
            <TrashIcon className="w-4 h-4 mr-2" />
            Delete Context
          </Button>
        </div>
      </div>
      <Fieldset aria-label="Add Contexts">
        {(experimentState as CMABExperimentState).contexts.map(
          (context, index) => (
            <div key={index}>
              <DividerWithTitle title={`Context ${index + 1}`} />
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
                          name={`context-${index + 1}-name`}
                          placeholder="Give the context a searchable name"
                          value={context.name || ""}
                          onChange={(e) => {
                            updateContext(index, { name: e.target.value });
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
                          name={`context-${index + 1}-description`}
                          placeholder="Describe the context"
                          value={context.description || ""}
                          onChange={(e) => {
                            updateContext(index, {
                              description: e.target.value,
                            });
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
                      <Label
                        className="basis-1/4 mt-3 font-medium"
                        htmlFor="mu"
                      >
                        Context type
                      </Label>
                      <div className="basis-3/4 flex flex-col">
                        <RadioGroup
                          name={`context-${index}-value-type`}
                          defaultValue=""
                          value={context.value_type || ""}
                          onChange={(value) => {
                            updateContext(index, {
                              value_type: value as ContextType,
                            });
                          }}
                        >
                          <div className="space-y-2">
                            <RadioField className="flex items-start space-x-2 rounded-md border border-gray-800 p-3 transition-colors data-[state=checked]:border-primary data-[state=checked]:border-2 hover:bg-transparent">
                              <Radio
                                id={`context-${index}-binary`}
                                value="binary"
                              />
                              <div className="flex flex-col">
                                <Label
                                  htmlFor={`context-${index}-binary`}
                                  className="font-medium"
                                >
                                  Binary
                                </Label>
                              </div>
                            </RadioField>

                            <RadioField className="flex items-start space-x-2 rounded-md border border-gray-800 p-3 transition-colors data-[state=checked]:border-primary data-[state=checked]:border-2 hover:bg-transparent">
                              <Radio
                                id={`context-${index}-real-valued`}
                                value="real-valued"
                              />
                              <div className="flex flex-col">
                                <Label
                                  htmlFor={`context-${index}-real-valued`}
                                  className="font-medium"
                                >
                                  Real-valued
                                </Label>
                              </div>
                            </RadioField>
                          </div>
                        </RadioGroup>

                        {errors[index]?.value_type ? (
                          <p className="text-red-500 text-xs mt-1">
                            {errors[index].value_type}
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
          )
        )}
      </Fieldset>
    </div>
  );
}
