import { useExperiment } from "./AddExperimentContext";
import { Heading } from "@/components/catalyst/heading";
import {
  Checkbox,
  CheckboxField,
  CheckboxGroup,
} from "@/components/catalyst/checkbox";
import { Description, Fieldset, Label } from "@/components/catalyst/fieldset";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function AddNotifications() {
  const { experimentState, setExperimentState } = useExperiment();
  const notifications = experimentState.notifications;
  const [trialCount, setTrialCount] = useState(1000);
  const [dayCount, setDayCount] = useState(30);
  const [eventPercent, setEventPercent] = useState(20);

  const inputClasses = `
    w-16 mx-1 px-1 py-0 h-6 inline-block font-bold rounded-none
    border-0 border-b-4 border-zinc-200 text-center
    focus:border-primary focus:border-0 focus:border-b-2 focus:ring-0 focus:ring-offset-0
    shadow-none appearance-none [&::-webkit-outer-spin-button]:appearance-none
    [&::-webkit-inner-spin-button]:appearance-none
    [-moz-appearance:textfield]
  `;

  return (
    <div>
      <div className="pt-5 flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <Heading>Select notifications</Heading>
      </div>
      <Fieldset aria-label="select notications" className="pt-6">
        <CheckboxGroup>
          <CheckboxField>
            <Checkbox name="discoverability" value="sample" defaultChecked />
            <Label>
              After
              <Input
                type="number"
                value={trialCount}
                onChange={(e) => setTrialCount(Number(e.target.value))}
                className={inputClasses}
                onClick={(e) => e.stopPropagation()}
              />
              {" trials"}
            </Label>
            <Description>
              Notify me when <b>{trialCount}</b> trials have been run
            </Description>
          </CheckboxField>
          <CheckboxField>
            <Checkbox name="discoverability" value="time" />
            <Label>
              After
              <Input
                type="number"
                value={dayCount}
                onChange={(e) => setDayCount(Number(e.target.value))}
                className={inputClasses}
                onClick={(e) => e.stopPropagation()}
              />
              {" days"}
            </Label>
            <Description>
              Notify me when <b>{dayCount}</b> days have passed since the
              experiment started
            </Description>
          </CheckboxField>
          <CheckboxField>
            <Checkbox name="discoverability" value="event" />
            <Label>
              If an arm is superior by
              <Input
                type="number"
                value={eventPercent}
                onChange={(e) => setEventPercent(Number(e.target.value))}
                className={inputClasses}
                onClick={(e) => e.stopPropagation()}
              />
              {"%"}
            </Label>
            <Description>
              Notify me if an arm is <b>{eventPercent}</b>% better than the
              other arms
            </Description>
          </CheckboxField>
        </CheckboxGroup>
      </Fieldset>
    </div>
  );
}
