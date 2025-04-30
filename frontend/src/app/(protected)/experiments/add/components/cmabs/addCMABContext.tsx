import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useExperimentStore } from "../../../store/useExperimentStore";
import type {
  CMABExperimentState,
  StepComponentProps,
  ContextType,
} from "../../../types";
import { Plus, Trash } from "lucide-react";
import { DividerWithTitle } from "@/components/Dividers";
import { useCallback, useEffect, useState } from "react";

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
        <h2 className="text-2xl font-semibold tracking-tight">
          Add CMAB Contexts
        </h2>
        <div className="flex gap-4">
          <Button className="mt-4" onClick={addContext}>
            <Plus className="w-4 h-4 mr-2" />
            Add Context
          </Button>
          <Button
            className="mt-4 mx-4"
            disabled={
              (experimentState as CMABExperimentState).contexts.length <= 1
            }
            variant="outline"
            onClick={() =>
              removeContext(
                (experimentState as CMABExperimentState).contexts.length - 1
              )
            }
          >
            <Trash className="w-4 h-4 mr-2" />
            Delete Context
          </Button>
        </div>
      </div>
      <div className="space-y-6" aria-label="Add Contexts">
        {(experimentState as CMABExperimentState).contexts.map(
          (context, index) => (
            <div key={index}>
              <DividerWithTitle title={`Context ${index + 1}`} />
              <div className="md:flex md:flex-row md:space-x-8 md:space-y-0 items-start">
                <div className="basis-1/2">
                  <div className="flex flex-col mb-4">
                    <div className="flex flex-row items-start">
                      <Label
                        className="basis-1/4 mt-2 font-medium"
                        htmlFor={`context-${index + 1}-name`}
                      >
                        Name
                      </Label>
                      <div className="basis-3/4 flex flex-col">
                        <Input
                          id={`context-${index + 1}-name`}
                          name={`context-${index + 1}-name`}
                          placeholder="Give the context a searchable name"
                          value={context.name || ""}
                          onChange={(e) => {
                            updateContext(index, { name: e.target.value });
                          }}
                        />
                        {errors[index]?.name ? (
                          <p className="text-destructive text-xs mt-1">
                            {errors[index].name}
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
                        htmlFor={`context-${index + 1}-description`}
                      >
                        Description
                      </Label>
                      <div className="basis-3/4 flex flex-col">
                        <Textarea
                          id={`context-${index + 1}-description`}
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
                          <p className="text-destructive text-xs mt-1">
                            {errors[index].description}
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

                <div className="basis-1/2 grow">
                  <div className="flex flex-col mb-4">
                    <div className="flex flex-row items-start">
                      <Label className="basis-1/4 mt-2 font-medium">
                        Context type
                      </Label>
                      <div className="basis-3/4 flex flex-col">
                        <RadioGroup
                          value={context.value_type || ""}
                          onValueChange={(value) => {
                            updateContext(index, {
                              value_type: value as ContextType,
                            });
                          }}
                          className="space-y-1/2"
                        >
                          <div className="flex items-start space-x-2 rounded-md border border-gray-800 p-3 transition-colors data-[state=checked]:border-primary data-[state=checked]:border-2 hover:bg-transparent">
                            <RadioGroupItem
                              value="binary"
                              id={`context-${index}-binary`}
                            />
                            <div className="flex flex-col items-start">
                              <Label
                                htmlFor={`context-${index}-binary`}
                                className="font-medium"
                              >
                                Binary
                              </Label>
                            </div>
                          </div>

                          <div className="flex items-start space-x-2 rounded-md border border-gray-800 p-3 transition-colors data-[state=checked]:border-primary data-[state=checked]:border-2 hover:bg-transparent">
                            <RadioGroupItem
                              value="real-valued"
                              id={`context-${index}-real-valued`}
                            />
                            <div className="flex flex-col items-start">
                              <Label
                                htmlFor={`context-${index}-real-valued`}
                                className="font-medium"
                              >
                                Real-valued
                              </Label>
                            </div>
                          </div>
                        </RadioGroup>

                        {errors[index]?.value_type ? (
                          <p className="text-destructive text-xs mt-1">
                            {errors[index].value_type}
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
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
}
