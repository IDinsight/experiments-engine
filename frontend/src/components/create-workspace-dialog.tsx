"use client";

import { useState } from "react";
import { apiCalls } from "@/utils/api";
import { useAuth } from "@/utils/auth";
import { useToast } from "@/hooks/use-toast";
import { useRouter } from "next/navigation";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

// Create schema for workspace form
const WorkspaceFormSchema = z.object({
  workspaceName: z
    .string()
    .min(3, "Workspace name must be at least 3 characters")
    .max(50, "Workspace name must be less than 50 characters"),
  apiDailyQuota: z
    .number()
    .int("API quota must be an integer")
    .min(1, "API quota must be at least 1")
    .optional(),
  contentQuota: z
    .number()
    .int("Content quota must be an integer")
    .min(1, "Content quota must be at least 1")
    .optional(),
});

type WorkspaceFormValues = z.infer<typeof WorkspaceFormSchema>;

interface CreateWorkspaceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateWorkspaceDialog({
  open,
  onOpenChange,
}: CreateWorkspaceDialogProps) {
  const { token, fetchWorkspaces } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [isCreating, setIsCreating] = useState(false);

  // Initialize form
  const form = useForm<WorkspaceFormValues>({
    resolver: zodResolver(WorkspaceFormSchema),
    defaultValues: {
      workspaceName: "",
      apiDailyQuota: undefined,
      contentQuota: undefined,
    },
  });

  async function onSubmit(data: WorkspaceFormValues) {
    if (!token) return;

    setIsCreating(true);
    try {
      await apiCalls.createWorkspace(
        token,
        data.workspaceName,
        data.apiDailyQuota,
        data.contentQuota
      );

      toast({
        title: "Workspace created",
        description: `${data.workspaceName} workspace was created successfully.`,
        variant: "success",
      });

      // Refresh the workspaces list
      await fetchWorkspaces();

      // Close the dialog and reset form
      onOpenChange(false);
      form.reset();

      // Navigate to workspaces page
      router.push("/workspaces");
    } catch (error: Error | unknown) {
      const errorMessage = error instanceof Error ? error.message : "Failed to create workspace. Please try again.";
      toast({
        title: "Error creating workspace",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New Workspace</DialogTitle>
          <DialogDescription>
            Create a new workspace for your team or project
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="workspaceName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Workspace Name</FormLabel>
                  <FormControl>
                    <Input placeholder="My New Workspace" {...field} />
                  </FormControl>
                  <FormDescription>
                    This is the name that will be displayed for your workspace
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button type="submit" disabled={isCreating}>
                {isCreating ? "Creating..." : "Create Workspace"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
