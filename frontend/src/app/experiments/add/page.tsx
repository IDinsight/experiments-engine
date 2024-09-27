"use client";
import {
  Description,
  Field,
  FieldGroup,
  Fieldset,
  Label,
} from "@/components/catalyst/fieldset";
import { Input } from "@/components/catalyst/input";
import { Divider } from "@/components/catalyst/divider";
import { Textarea } from "@/components/catalyst/textarea";
import { Radio, RadioField, RadioGroup } from "@/components/catalyst/radio";
import { useState } from "react";
import { Button } from "@/components/catalyst/button";
import { PlusIcon } from "@heroicons/react/16/solid";
import { DividerWithTitle } from "@/components/Dividers";
import { Heading } from "@/components/catalyst/heading";
import { NewArm, NewMAB } from "../types";
import { createMABExperiment } from "../api";
import { a } from "framer-motion/client";
import { useRouter } from "next/navigation";
import { useAuth } from "@/utils/auth";

const defaultArm: NewArm = {
  name: "",
  description: "",
  alpha_prior: 1,
  beta_prior: 1,
};

export default function NewExperiment() {
  const router = useRouter();
  const { token } = useAuth();

  const [methodType, setMethodType] = useState("MAB");
  const [experimentName, setExperimentName] = useState<string>("");
  const [experimentDescription, setExperimentDescription] =
    useState<string>("");
  const [arms, setArms] = useState<NewArm[]>([
    { ...defaultArm },
    { ...defaultArm },
  ]);

  const onSubmit = () => {
    const mab: NewMAB = {
      name: experimentName,
      description: experimentDescription,
      arms: arms,
    };

    createMABExperiment({ mab, token })
      .then((response) => {
        console.log(response);
        router.push(`/experiments`);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  return (
    <>
      <Heading className="mb-8">Create New Experiment</Heading>
      <form action="/orders" method="POST">
        <Fieldset aria-label="New Experiment">
          <FieldGroup>
            <Field>
              <Label>Experiment Name</Label>
              <Input
                name="experiment-name"
                placeholder="Give it a name you'll remember"
                onChange={(e) => setExperimentName(e.target.value)}
              />
            </Field>
            <Field>
              <Label>Description</Label>
              <Textarea
                name="experiment-description"
                placeholder="Why are you running this experiment? What do you wish to test?"
                rows={3}
                onChange={(e) => setExperimentDescription(e.target.value)}
              />
            </Field>
          </FieldGroup>
          <Divider className="mt-8" />
          <RadioGroup
            name="experiment-method"
            defaultValue="MAB"
            onChange={(value) => setMethodType(value)}
          >
            <Label>Select experiment type</Label>
            <RadioField>
              <Radio id="mab" value="MAB" />
              <Label htmlFor="mab">Multi-armed Bandit</Label>
              <Description>
                A method that automatically converges to the best performing
                arm.
              </Description>
            </RadioField>
            <RadioField>
              <Radio id="ab-test" value="AB" disabled />
              <Label htmlFor="ab-test">[Coming soon] A/B Testing</Label>
              <Description>
                A method that compares two or more variants against each other.
              </Description>
            </RadioField>
          </RadioGroup>
          <Divider className="mt-8" />
          <Button
            className="mt-4"
            onClick={() => setArms([...arms, { ...defaultArm }])}
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Add Arm
          </Button>
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
                        setArms(newArms);
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
                        setArms(newArms);
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
                        setArms(newArms);
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
                        setArms(newArms);
                      }}
                    />
                  </Field>
                </div>
              </FieldGroup>
            </div>
          ))}
          <div className="flex justify-center mt-10">
            <button
              type="button"
              className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              onClick={() => onSubmit()}
            >
              <PlusIcon aria-hidden="true" className="-ml-0.5 mr-1.5 h-5 w-5" />
              Create Experiment
            </button>
          </div>
        </Fieldset>
      </form>
    </>
  );
}
