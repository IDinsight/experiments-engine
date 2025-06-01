"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/utils/auth";
import { apiCalls } from "@/utils/api";
import { useToast } from "@/hooks/use-toast";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { ChevronLeftIcon, Send, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Create schema for invitation form
const InviteFormSchema = z.object({
  email: z
    .string()
    .email("Please enter a valid email address"),
  role: z
    .string()
    .refine(val => ["admin", "read_only"].includes(val), {
      message: "Please select a valid role",
    }),
});

type InviteFormValues = z.infer<typeof InviteFormSchema>;

export default function InviteUserPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuth();
  const { toast } = useToast();
  const [isInviting, setIsInviting] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState(false);

  const workspaceId = Number(params.workspaceId);

  // Initialize form
  const form = useForm<InviteFormValues>({
    resolver: zodResolver(InviteFormSchema),
    defaultValues: {
      email: "",
      role: "read_only", // Default to read-only
    },
  });

  const onSubmit = async (data: InviteFormValues) => {
    if (!token) return;

    setIsInviting(true);
    try {
      // First need to get workspace name
      const workspace = await apiCalls.getWorkspaceById(token, workspaceId);

      // Send invitation
      await apiCalls.inviteUserToWorkspace(
        token,
        data.email,
        workspace.workspace_name,
        data.role
      );

      // Show success message
      setInviteSuccess(true);
      toast({
        title: "Invitation sent",
        description: `${data.email} has been invited to the workspace`,
        variant: "success",
      });

      // Reset form
      form.reset();
    } catch (error: Error | unknown) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send invitation",
        variant: "destructive",
      });
    } finally {
      setIsInviting(false);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/">Home</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink href="/workspaces">Workspaces</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink href={`/workspaces/${workspaceId}`}>Workspace</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>Invite User</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <div className="p-2 bg-muted rounded-md mr-3">
            <Users className="h-6 w-6" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Invite User</h1>
        </div>
        <Button variant="outline" onClick={() => router.back()}>
          <ChevronLeftIcon className="mr-2 h-4 w-4" />
          Back
        </Button>
      </div>

      <Card className="max-w-md mx-auto">
        <CardHeader>
          <CardTitle>Invite User to Workspace</CardTitle>
          <CardDescription>
            Send an invitation to join this workspace
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input placeholder="user@example.com" {...field} />
                    </FormControl>
                    <FormDescription>
                      The email address of the person you want to invite
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="role"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Role</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a role" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="admin">Administrator</SelectItem>
                        <SelectItem value="read_only">Regular User</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Administrators can manage workspace settings and users. Regular users have read-only access.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button
                type="submit"
                className="w-full"
                disabled={isInviting}
              >
                <Send className="mr-2 h-4 w-4" />
                {isInviting ? "Sending Invitation..." : "Send Invitation"}
              </Button>
            </form>
          </Form>

          {inviteSuccess && (
            <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 rounded-md border border-green-200 dark:border-green-800">
              <h4 className="font-medium text-green-900 dark:text-green-500">
                Invitation Sent Successfully
              </h4>
              <p className="text-sm text-green-700 dark:text-green-400 mt-1">
                An email has been sent to the user with instructions to join the workspace.
              </p>
            </div>
          )}
        </CardContent>
        <CardFooter>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => router.push(`/workspaces/${workspaceId}`)}
          >
            Return to Workspace
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
