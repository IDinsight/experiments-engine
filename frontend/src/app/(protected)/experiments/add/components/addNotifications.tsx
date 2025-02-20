import { useExperiment } from "./AddExperimentContext";
import { Heading } from "@/components/catalyst/heading";
import {
  Checkbox,
  CheckboxField,
  CheckboxGroup,
} from "@/components/catalyst/checkbox";
import { Description, Fieldset, Label } from "@/components/catalyst/fieldset";
export default function AddNotifications() {
  const { experimentState, setExperimentState } = useExperiment();
  const notifications = experimentState.notifications;

  return (
    <div>
      <div className="pt-5 flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <Heading>Select notifications</Heading>
      </div>
      <Fieldset aria-label="select notications" className="pt-6">
        <CheckboxGroup>
          <CheckboxField>
            <Checkbox name="discoverability" value="sample" defaultChecked />
            <Label>After X trails</Label>
            <Description>Notify me when X trials have been run</Description>
          </CheckboxField>
          <CheckboxField>
            <Checkbox name="discoverability" value="time" />
            <Label>After X days</Label>
            <Description>
              Notify me when X days have passed since the experiment started
            </Description>
          </CheckboxField>
          <CheckboxField>
            <Checkbox name="discoverability" value="event" />
            <Label>If an arm is superior by X%</Label>
            <Description>
              Notify me if an arm is X% better than the other arms
            </Description>
          </CheckboxField>
        </CheckboxGroup>
      </Fieldset>
    </div>
  );
}
