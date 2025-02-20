"use client";
import { useState } from "react";
import { AllSteps } from "./components/addExperimentSteps";
import AddBasicInfo from "./components/basicInfo";
import { useExperiment } from "./components/AddExperimentContext";
import { Button } from "@/components/catalyst/button";
import {
  PlusIcon,
  ChevronRightIcon,
  ChevronLeftIcon,
} from "@heroicons/react/20/solid";
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

export default function NewExperiment() {
  const [currentStep, setCurrentStep] = useState(0);
  const { experimentState } = useExperiment();

  type Methods = typeof AllSteps;
  const [method, setMethod] = useState<keyof Methods>("mab");

  const steps = AllSteps[method];

  const nextStep = () =>
    setCurrentStep((prev) => Math.min(prev + 1, steps.length));
  const prevStep = () => setCurrentStep((prev) => Math.max(prev - 1, 0));

  const EmptyComponent: React.FC = () => <></>;
  const CurrentStepComponent: React.ComponentType =
    currentStep === 0 ? EmptyComponent : steps[currentStep - 1].component;
  const { token } = useAuth();
  const router = useRouter();

  const onSubmit = () => {
    createNewExperiment({ experimentData: experimentState, token })
      .then((response) => {
        console.log("Experiment created", response);
        router.push("/experiments");
      })
      .catch((error) => {
        console.error(error);
      });
  };
  return (
    <>
      <div className="max-w-4xl mx-auto">
        <div className="text-zinc-800 mb-4">
          <Breadcrumb>
            <BreadcrumbList>
              {currentStep === 0 ? (
                <BreadcrumbItem>
                  <BreadcrumbPage className="font-semibold">
                    Basic Details
                  </BreadcrumbPage>
                </BreadcrumbItem>
              ) : (
                <BreadcrumbItem>
                  <BreadcrumbLink onClick={() => setCurrentStep(0)}>
                    Basic Details
                  </BreadcrumbLink>
                </BreadcrumbItem>
              )}

              <BreadcrumbSeparator>
                <ChevronRightIcon className="h-5 w-5 text-zinc-800" />
              </BreadcrumbSeparator>
              {steps.slice(0, currentStep).map((step, index) =>
                index < currentStep - 1 ? (
                  <>
                    <BreadcrumbItem key={index}>
                      <BreadcrumbLink onClick={() => setCurrentStep(index + 1)}>
                        {step.name}
                      </BreadcrumbLink>
                    </BreadcrumbItem>

                    <BreadcrumbSeparator>
                      <ChevronRightIcon className="h-5 w-5 text-zinc-800" />
                    </BreadcrumbSeparator>
                  </>
                ) : (
                  <>
                    <BreadcrumbItem key={index}>
                      <BreadcrumbPage className="text-zinc-800 font-semibold ">
                        {step.name}
                      </BreadcrumbPage>
                    </BreadcrumbItem>
                    {index < currentStep - 1 && (
                      <BreadcrumbSeparator>
                        <ChevronRightIcon className="h-5 w-5 text-zinc-800" />
                      </BreadcrumbSeparator>
                    )}
                  </>
                ),
              )}
            </BreadcrumbList>
          </Breadcrumb>
        </div>
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
          <ChevronLeftIcon className="h-5 w-5" />
          Previous
        </Button>
        {currentStep === steps.length ? (
          <button
            type="button"
            className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            onClick={onSubmit}
          >
            <PlusIcon aria-hidden="true" className="-ml-0.5 mr-1.5 h-5 w-5" />
            Create Experiment
          </button>
        ) : (
          <Button className="px-4 py-2 bg-gray-200 rounded" onClick={nextStep}>
            Next
            <ChevronRightIcon className="h-5 w-5" />
          </Button>
        )}
      </div>
    </>
  );
}
