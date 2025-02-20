"use client";
import { useState } from "react";
import { AllSteps } from "./addExperimentSteps";
import { ExperimentProvider } from "./components/AddExperimentContext";
import AddBasicInfo from "./components/basicInfo";
import { Button } from "@/components/catalyst/button";

export default function NewExperiment() {
  const [currentStep, setCurrentStep] = useState(0);
  type Methods = typeof AllSteps;
  const [method, setMethod] = useState<keyof Methods>("mab");

  const steps = AllSteps[method];

  const nextStep = () =>
    setCurrentStep((prev) => Math.min(prev + 1, steps.length));
  const prevStep = () => setCurrentStep((prev) => Math.max(prev - 1, 0));

  const EmptyComponent: React.FC = () => <></>;
  const CurrentStepComponent: React.ComponentType =
    currentStep === 0 ? EmptyComponent : steps[currentStep - 1].component;

  return (
    <ExperimentProvider>
      <div className="max-w-4xl mx-auto">
        {currentStep === 0 ? (
          <AddBasicInfo
            setMethodType={(method) => setMethod(method as keyof Methods)}
          />
        ) : (
          <CurrentStepComponent />
        )}
      </div>
      <div className="flex justify-between max-w-4xl mx-auto mt-8">
        <Button onClick={prevStep} disabled={currentStep === 0}>
          Previous
        </Button>
        <Button
          className="px-4 py-2 bg-gray-200 rounded"
          onClick={nextStep}
          disabled={currentStep === steps.length}
        >
          Next
        </Button>
      </div>
    </ExperimentProvider>
  );
}
