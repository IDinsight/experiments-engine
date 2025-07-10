"use client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useExperimentStore } from "../../store/useExperimentStore";
import {
  CheckCircle, AlertCircle, Rocket, FlaskConical, Target,
  Bell, Users, Settings, Sparkles, Eye
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function ExperimentSummary() {
  const { experimentState, aiWizardState } = useExperimentStore();

  const isFormValid =
    !!experimentState.name?.trim() &&
    !!experimentState.description?.trim() &&
    experimentState.arms.length > 0 &&
    experimentState.arms.every(arm => !!arm.name?.trim());


  const getMethodTypeLabel = (type: string) => {
    const labels: { [key: string]: string } = {
      mab: "Multi-Armed Bandit",
      cmab: "Contextual Multi-Armed Bandit",
      bayes_ab: "Bayesian A/B Test",
    };
    return labels[type] || type;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-8">
      <div className="space-y-3 bg-gradient-to-r from-primary/5 to-transparent p-6 rounded-lg">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <div className="bg-primary/10 p-2 rounded-full">
            <Eye className="h-6 w-6 text-primary" />
          </div>
          Review & Create
        </h1>
        <p className="text-muted-foreground text-lg">
          Please review all the details below before creating your experiment.
        </p>
      </div>

      {!isFormValid && (
        <Alert variant="destructive" className="border-2 shadow-md">
          <AlertCircle className="h-5 w-5" />
          <AlertDescription className="font-medium">
            Some required information is missing. Please go back to previous steps to complete the setup.
          </AlertDescription>
        </Alert>
      )}

      <Card className="overflow-hidden border-2 transition-all hover:shadow-md">
        <div className="h-1.5 "></div>
        <CardHeader className=" pb-3">
          <CardTitle className="flex items-center gap-2 text-xl">
            <FlaskConical className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            Basic Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-5 ">
          <div className="grid md:grid-cols-2 gap-5">
            <div>
              <label className="text-sm uppercase tracking-wider font-medium text-muted-foreground">Experiment Name</label>
              <p className="font-semibold text-lg mt-1">{experimentState.name || "Not specified"}</p>
            </div>
            <div>
              <label className="text-sm uppercase tracking-wider font-medium text-muted-foreground">Experiment Type</label>
              <p className="mt-1">
                <Badge variant="secondary" className="text-sm px-3 py-1">
                  {getMethodTypeLabel(experimentState.exp_type)}
                </Badge>
              </p>
            </div>
          </div>

          <div>
            <label className="text-sm uppercase tracking-wider font-medium text-muted-foreground">Description</label>
            <p className="mt-1 p-3 bg-muted/30 rounded-md border border-muted">
              {experimentState.description || "Not specified"}
            </p>
          </div>

          {aiWizardState.goal && (
            <div className="bg-muted/50 p-4 rounded-md border border-border shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <div className="bg-primary/10 p-1.5 rounded-full">
                  <Sparkles className="h-4 w-4 text-primary" />
                </div>
                <h4 className="font-medium">AI Generated Experiment</h4>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="p-3 rounded-md border">
                  <p className="text-sm leading-relaxed">
                    <span className="font-semibold text-primary/90 block mb-1">Goal</span>
                    {aiWizardState.goal}
                  </p>
                </div>
                <div className="p-3 rounded-md border">
                  <p className="text-sm leading-relaxed">
                    <span className="font-semibold text-primary/90 block mb-1">Outcome</span>
                    {aiWizardState.outcome}
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="overflow-hidden border-2 transition-all hover:shadow-md">
        <CardHeader >
          <CardTitle className="flex items-center gap-2 text-xl">
            <Settings className="h-5 w-5 text-green-600 dark:text-green-400" />
            Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
            <div>
              <label className="text-sm uppercase tracking-wider font-medium text-muted-foreground">Prior Type</label>
              <p className="capitalize text-lg mt-1 font-medium">{experimentState.prior_type}</p>
            </div>
            <div>
              <label className="text-sm uppercase tracking-wider font-medium text-muted-foreground">Reward Type</label>
              <p className="capitalize text-lg mt-1 font-medium">{experimentState.reward_type}</p>
            </div>
            <div>
              <label className="text-sm uppercase tracking-wider font-medium text-muted-foreground">Sticky Assignment</label>
              <p className="mt-1 flex items-center gap-2">
                {experimentState.sticky_assignment ?
                  <><CheckCircle className="h-4 w-4 text-green-500" /> Enabled</> :
                  <span className="text-muted-foreground">Disabled</span>}
              </p>
            </div>
            <div>
              <label className="text-sm uppercase tracking-wider font-medium text-muted-foreground">Auto-Fail</label>
              <p className="mt-1">
                {experimentState.auto_fail ?
                  <Badge variant="outline">{`${experimentState.auto_fail_value} ${experimentState.auto_fail_unit}`}</Badge> :
                  <span className="text-muted-foreground">Disabled</span>}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="overflow-hidden border-2 transition-all hover:shadow-md">
        <CardHeader >
          <CardTitle className="flex items-center gap-2 text-xl">
            <Users className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            Experiment Arms
            <Badge className="ml-2">{experimentState.arms.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="">
          <div className="grid md:grid-cols-2 gap-3">
            {experimentState.arms.map((arm, index) => (
              <div key={index} className="border-2 border-dashed border-muted p-4 rounded-md hover:border-primary/30 transition-colors">
                <div className="flex justify-between items-center mb-2">
                  <p className="font-semibold">{arm.name || `Arm ${index + 1}`}</p>
                  <Badge variant="outline" className="text-xs">Arm {index + 1}</Badge>
                </div>
                <p className="text-sm text-muted-foreground">{arm.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {experimentState.exp_type === 'cmab' && experimentState.contexts && experimentState.contexts.length > 0 && (
        <Card className="overflow-hidden border-2 transition-all hover:shadow-md">
          <CardHeader >
            <CardTitle className="flex items-center gap-2 text-xl">
              <Target className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
              Contexts
              <Badge className="ml-2">{experimentState.contexts.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="">
            <div className="grid md:grid-cols-2 gap-3">
              {experimentState.contexts.map((context, index) => (
                <div key={index} className="bg-muted/30 p-4 rounded-md border">
                  <div className="flex justify-between items-center mb-2">
                    <p className="font-semibold">{context.name}</p>
                    <Badge variant="outline" className="capitalize text-xs">{context.value_type}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{context.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="overflow-hidden border-2 transition-all hover:shadow-md">
        <CardHeader >
          <CardTitle className="flex items-center gap-2 text-xl">
            <Bell className="h-5 w-5 text-red-600 dark:text-red-400" />
            Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="">
          <div className="grid md:grid-cols-3 gap-3">
            <div className="p-3 bg-muted/30 rounded-md border">
              <h4 className="font-medium mb-1 text-sm">Trial Completion</h4>
              {experimentState.notifications.onTrialCompletion ? (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  {experimentState.notifications.numberOfTrials} trials
                </Badge>
              ) : (
                <Badge variant="outline" className="text-muted-foreground">Disabled</Badge>
              )}
            </div>
            <div className="p-3 bg-muted/30 rounded-md border">
              <h4 className="font-medium mb-1 text-sm">Days Elapsed</h4>
              {experimentState.notifications.onDaysElapsed ? (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  {experimentState.notifications.daysElapsed} days
                </Badge>
              ) : (
                <Badge variant="outline" className="text-muted-foreground">Disabled</Badge>
              )}
            </div>
            <div className="p-3 bg-muted/30 rounded-md border">
              <h4 className="font-medium mb-1 text-sm">Percent Better</h4>
              {experimentState.notifications.onPercentBetter ? (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  {experimentState.notifications.percentBetterThreshold}%
                </Badge>
              ) : (
                <Badge variant="outline" className="text-muted-foreground">Disabled</Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {isFormValid && (
        <Alert className="border-green-300 bg-green-50 dark:border-green-800 dark:bg-green-900/20 shadow-md">
          <Rocket className="h-5 w-5 text-green-600" />
          <AlertDescription className="font-medium text-green-800 dark:text-green-300">
            You're all set! Click the "Create Experiment" button to launch your experiment.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
