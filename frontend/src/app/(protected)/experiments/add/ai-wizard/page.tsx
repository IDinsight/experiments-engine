"use client";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useRouter } from "next/navigation";
import { useExperimentStore } from "../../store/useExperimentStore";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { HelpCircle, Sparkles, ArrowRight, Wand2, FlaskConical } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

export default function AIWizardPage() {
  const router = useRouter();
  const {
    updateName,
    updateDescription,
    updateMethodType,
    updateArms,
    updateContexts,
    aiWizardState,
    updateAIGoal,
    updateAIOutcome,
    updateAINumVariants,
    resetState
  } = useExperimentStore();


  useEffect(() => {
    resetState();
  }, []);

  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch('http://localhost:8000/ai_helpers/generate-whole-experiment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goal: aiWizardState.goal,
          outcome: aiWizardState.outcome,
          num_variants: aiWizardState.numVariants,
        }),
      });

      if (response.ok) {
        const aiData = await response.json();

        updateName(aiData.name);
        updateDescription(aiData.description);
        updateMethodType(aiData.experiment_type);

        if (aiData.arms && Array.isArray(aiData.arms)) {
          updateArms(aiData.arms);
        }

        if (aiData.contexts && Array.isArray(aiData.contexts)) {
          updateContexts(aiData.contexts);
        }

        router.push("/experiments/add");
      } else {
        console.error("AI generation failed with status:", response.status);
      }
    } catch (error) {
      console.error("AI generation failed:", error);
    } finally {
      setIsGenerating(false);
    }
  };

  const isFormValid = aiWizardState.goal.trim() && aiWizardState.outcome.trim() && aiWizardState.numVariants >= 2;

  return (
    <TooltipProvider>
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <Breadcrumb className="mb-6">
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/experiments">Experiments</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink href="/experiments/add">Create</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbPage>AI Wizard</BreadcrumbPage>
          </BreadcrumbList>
        </Breadcrumb>

        <div className="text-center space-y-3 mb-8">
          <div className="flex items-center justify-center gap-2">
            <h1 className="text-3xl font-bold tracking-tight">AI Experiment Wizard</h1>
          </div>
          <p className="text-lg text-muted-foreground">
            Answer a few questions and we'll design your experiment
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <Card className="border-2">
              <CardHeader className="pb-4">
                <div className="flex items-center gap-2">
                  <FlaskConical className="h-5 w-5 text-primary" />
                  <CardTitle className="text-xl">Experiment Details</CardTitle>
                </div>
                <CardDescription className="text-base">
                  Answer these questions to help AI design your experiment
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-8">
                <div className="space-y-3">
                  <div className="flex items-start gap-2">
                    <label className="block font-semibold text-base leading-relaxed">
                      What goal do you want to achieve with your experiment?
                    </label>
                    <Tooltip>
                      <TooltipTrigger>
                        <HelpCircle className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs bg-black/50 text-sm border-[0.9px] border-white/50 text-white backdrop-blur-sm">
                        <p>
                          Examples: Increase sign-ups by testing a new onboarding flow; reduce drop-off by changing message timing; improve engagement by using a casual tone for youth users.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </div>
                  <Textarea
                    value={aiWizardState.goal}
                    onChange={e => updateAIGoal(e.target.value)}
                    placeholder="E.g., Increase sign-ups by testing a new onboarding flow. Reduce drop-off by changing message timing. Improve engagement by using a casual tone for youth users."
                    rows={4}
                    className="resize-none text-base"
                  />
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                    Required field
                  </div>
                </div>

                <Separator />

                <div className="space-y-3">
                  <div className="flex items-start gap-2">
                    <label className="block font-semibold text-base leading-relaxed">
                      What outcome will you measure to know if your idea works? (What decision will you make based on this?)
                    </label>
                    <Tooltip>
                      <TooltipTrigger>
                        <HelpCircle className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs bg-black/50 text-sm border-[0.9px] border-white/50 text-white backdrop-blur-sm">
                        <p>
                          Examples: Completion rate (% who finish), click rate (% who click), time spent, engagement score, drop-off rate. What will you do if the outcome improves?
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </div>
                  <Input
                    value={aiWizardState.outcome}
                    onChange={e => updateAIOutcome(e.target.value)}
                    placeholder="E.g., Completion rate, engagement score, time spent, drop-off rate, clicks. If completion rate improves, roll out new onboarding to all users."
                    className="text-base"
                  />
                  <p className="text-sm text-muted-foreground">
                    This should be something you can measure on your platform.
                  </p>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                    Required field
                  </div>
                </div>

                <Separator />

                <div className="space-y-3">
                  <div className="flex items-start gap-2">
                    <label className="block font-semibold text-base leading-relaxed">
                      How many different "variants" (arms) will you be testing? (e.g. 2 for A/B, 3+ for multivariate)
                    </label>
                    <Tooltip>
                      <TooltipTrigger>
                        <HelpCircle className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs bg-black/50 text-sm border-[0.9px] border-white/50 text-white backdrop-blur-sm">
                        <p>
                          Variants are the different versions you want to compare. For example: Variant 1 - current button, Variant 2 - new red button, Variant 3 - new blue button.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </div>
                  <Input
                    type="number"
                    min={2}
                    max={6}
                    value={aiWizardState.numVariants}
                    onChange={e => updateAINumVariants(Number(e.target.value))}
                    className="w-24 text-base text-center"
                    placeholder="E.g., 2 for A/B test, 3 for multivariate"
                  />
                  <p className="text-sm text-muted-foreground">
                    Usually 2-4 variants work best. More variants need more users to get reliable results.
                  </p>
                </div>

              </CardContent>
            </Card>

            <div className="flex gap-4">
              <Button
                onClick={handleGenerate}
                disabled={!isFormValid || isGenerating}
                className="flex-1 h-12 text-base"
                size="lg"
              >
                {isGenerating ? (
                  <>
                    <Sparkles className="h-4 w-4 mr-2 animate-spin" />
                    Generating Experiment...
                  </>
                ) : (
                  <>
                    <Wand2 className="h-4 w-4 mr-2" />
                    Generate My Experiment
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => router.push("/experiments/add")}
                className="h-12"
                size="lg"
              >
                Skip AI
              </Button>
            </div>
          </div>

          <div className="space-y-6">
            <Card className="bg-muted/30">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Sparkles className="h-4 w-4" />
                  How it works
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                      1
                    </div>
                    <div>
                      <p className="font-medium">Describe your idea</p>
                      <p className="text-sm text-muted-foreground">Tell us what you want to test</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                      2
                    </div>
                    <div>
                      <p className="font-medium">Set your goal</p>
                      <p className="text-sm text-muted-foreground">Define what success looks like</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                      3
                    </div>
                    <div>
                      <p className="font-medium">Get AI suggestions</p>
                      <p className="text-sm text-muted-foreground">We'll create experiment details for you</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}
