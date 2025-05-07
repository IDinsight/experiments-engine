"use client";
import React from "react";
import { useState, useCallback, useEffect } from "react";
import { AllSteps } from "./components/addExperimentSteps";
import AddBasicInfo from "./components/basicInfo";
import { useExperimentStore } from "../store/useExperimentStore";
import { Button } from "@/components/ui/button";
import { PlusIcon, ChevronRightIcon, ChevronLeftIcon } from "lucide-react";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { useAuth } from "@/utils/auth";
import { useRouter } from "next/navigation";
import { createNewExperiment } from "../api";
import type { StepComponentProps, StepValidation } from "../types";
import { AnimatePresence, motion } from "framer-motion";
import { useToast } from "@/hooks/use-toast";

export default function NewExperiment() {
  const [currentStep, setCurrentStep] = useState(0);
  const [direction, setDirection] = useState(0); // 1 for forward, -1 for backward
  const { experimentState, resetState } = useExperimentStore();
  const [stepValidations, setStepValidations] = useState<StepValidation[]>([]);
  const { token } = useAuth();
  const router = useRouter();

  const [steps, setSteps] = useState(AllSteps[experimentState.methodType]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { toast } = useToast();

  useEffect(() => {
    resetState();
  }, []);

  useEffect(() => {
    setSteps(AllSteps[experimentState.methodType]);
    setCurrentStep(0);
  }, [experimentState.methodType]);

  const nextStep = useCallback(() => {
    const currentValidation = stepValidations[currentStep];
    if (!currentValidation || !currentValidation.isValid) {
      console.log("Cannot proceed. Please fill in all required fields.");
      return;
    }
    setDirection(1); // Set direction to forward
    setCurrentStep((prev) => Math.min(prev + 1, steps.length));
  }, [currentStep, stepValidations, steps.length]);

  const prevStep = () => {
    setDirection(-1); // Set direction to backward
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  const EmptyComponent: React.FC<StepComponentProps> = () => null;
  const CurrentStepComponent: React.ComponentType<StepComponentProps> =
    currentStep === 0 ? EmptyComponent : steps[currentStep - 1].component;

  const onSubmit = () => {
    setIsSubmitting(true);
    if (stepValidations.every((validation) => validation.isValid)) {
      createNewExperiment({ experimentData: experimentState, token })
        .then((response) => {
          console.log("Experiment created", response);
          toast({
            title: `Experiment #${response.experiment_id} created`,
            description: "Your experiment has been successfully created.",
            variant: "success",
          });
          router.push("/experiments");
        })
        .catch((error) => {
          toast({
            title: "Error creating experiment",
            description: "An error occurred while creating the experiment.",
            variant: "destructive",
          });
          console.error(error);
        });
    } else {
      console.log("Cannot proceed. Please check all steps for errors.");
    }
    setIsSubmitting(false);
    resetState();
  };
  const handleStepValidation = useCallback(
    (stepIndex: number, validation: StepValidation) => {
      setStepValidations((prev) => {
        const newValidations = [...prev];
        newValidations[stepIndex] = validation;
        return newValidations;
      });
    },
    []
  );

  // Animation variants that change based on direction
  const pageVariants = {
    initial: (direction: number) => ({
      opacity: 0,
      x: direction > 0 ? 100 : -100, // Come from right when going forward, left when going backward
    }),
    animate: {
      opacity: 1,
      x: 0,
      transition: {
        type: "tween",
        ease: "easeInOut",
        duration: 0.3,
      },
    },
    exit: (direction: number) => ({
      opacity: 0,
      x: direction > 0 ? -100 : 100, // Exit to left when going forward, right when going backward
      transition: {
        type: "tween",
        ease: "easeInOut",
        duration: 0.3,
      },
    }),
  };

  return (
    <>
      <div className="max-w-4xl mx-auto">
        <div className="text-zinc-800 mb-4">
          <Breadcrumb>
            <BreadcrumbList>
              {currentStep === 0 ? (
                <BreadcrumbItem key="basic-details-current">
                  <BreadcrumbPage className="font-semibold">
                    Basic Details
                  </BreadcrumbPage>
                </BreadcrumbItem>
              ) : (
                <BreadcrumbItem
                  key="basic-details-link"
                  className="hover:cursor-pointer"
                >
                  <BreadcrumbLink
                    onClick={() => {
                      setDirection(-1);
                      setCurrentStep(0);
                    }}
                  >
                    Basic Details
                  </BreadcrumbLink>
                </BreadcrumbItem>
              )}

              <BreadcrumbSeparator key="first-separator">
                <ChevronRightIcon className="h-5 w-5 text-zinc-800 dark:text-zinc-200" />
              </BreadcrumbSeparator>
              {steps.slice(0, currentStep).map((step, index) => (
                <React.Fragment key={`step-${index}`}>
                  <BreadcrumbItem>
                    {index < currentStep - 1 ? (
                      <BreadcrumbLink
                        className="hover:cursor-pointer"
                        onClick={() => {
                          setDirection(index + 1 < currentStep ? -1 : 1);
                          setCurrentStep(index + 1);
                        }}
                      >
                        {step.name}
                      </BreadcrumbLink>
                    ) : (
                      <BreadcrumbPage className="text-zinc-800 font-semibold">
                        {step.name}
                      </BreadcrumbPage>
                    )}
                  </BreadcrumbItem>
                  {index < currentStep - 1 && (
                    <BreadcrumbSeparator key={`separator-${index}`}>
                      <ChevronRightIcon className="h-5 w-5 text-zinc-800 dark:text-zinc-200" />
                    </BreadcrumbSeparator>
                  )}
                </React.Fragment>
              ))}
            </BreadcrumbList>
          </Breadcrumb>
        </div>

        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={currentStep}
            custom={direction}
            initial="initial"
            animate="animate"
            exit="exit"
            variants={pageVariants}
          >
            {currentStep === 0 ? (
              <AddBasicInfo
                onValidate={(validation: StepValidation) =>
                  handleStepValidation(currentStep, validation)
                }
              />
            ) : (
              <CurrentStepComponent
                onValidate={(validation: StepValidation) =>
                  handleStepValidation(currentStep, validation)
                }
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="flex justify-between max-w-4xl mx-auto mt-8">
        <Button onClick={prevStep} disabled={currentStep === 0}>
          <ChevronLeftIcon className="h-5 w-5" />
          Previous
        </Button>
        {currentStep === steps.length ? (
          <button
            type="button"
            className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-xs hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={onSubmit}
            disabled={
              !stepValidations.every((validation) => validation.isValid) ||
              isSubmitting
            }
          >
            <PlusIcon aria-hidden="true" className="-ml-0.5 mr-1.5 h-5 w-5" />
            Create Experiment
          </button>
        ) : (
          <Button
            onClick={nextStep}
            disabled={!stepValidations[currentStep]?.isValid}
          >
            Next
            <ChevronRightIcon className="h-5 w-5" />
          </Button>
        )}
      </div>
    </>
  );
}
