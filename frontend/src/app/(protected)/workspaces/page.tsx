"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/utils/auth";
import { Building, Plus, Settings } from "lucide-react";
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
import Hourglass from "@/components/Hourglass";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import Link from "next/link";
import { CreateWorkspaceDialog } from "@/components/create-workspace-dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import router from "next/router";

export default function WorkspacesPage() {
  const { workspaces, currentWorkspace, fetchWorkspaces, switchWorkspace } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  useEffect(() => {
    const loadWorkspaces = async () => {
      setIsLoading(true);
      try {
        await fetchWorkspaces();
      } catch (error) {
        console.error("Error loading workspaces:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadWorkspaces();
  }, []);

  const handleWorkspaceSwitch = async (workspaceName: string) => {
    try {
      setIsLoading(true);
      await switchWorkspace(workspaceName);
    } catch (error) {
      console.error("Error switching workspace:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="rounded-lg bg-card p-6 flex flex-col items-center justify-center space-y-4 w-full max-w-sm mx-auto">
          <Hourglass />
          <span className="text-primary font-medium text-center">Loading workspaces...</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="container mx-auto py-8 px-4">
        <div className="mb-8">
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href="/">Home</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>Workspaces</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>

        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Workspaces</h1>
            <p className="text-muted-foreground">
              Manage your workspaces and team members
            </p>
          </div>
          <Button onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Workspace
          </Button>
        </div>

        <Tabs defaultValue="all">
          <TabsList className="mb-6">
            <TabsTrigger value="all">All Workspaces</TabsTrigger>
            <TabsTrigger value="current">Current Workspace</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {workspaces.map((workspace) => (
                <Card key={workspace.workspace_id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="relative">
                    <div className="absolute top-4 right-4">
                      {workspace.is_default && (
                        <Badge variant="secondary">Default</Badge>
                      )}
                      {currentWorkspace?.workspace_id === workspace.workspace_id && (
                        <Badge className="ml-2 bg-green-600">Current</Badge>
                      )}
                    </div>
                    <div className="flex items-center mb-2">
                      <div className="p-2 bg-muted rounded-md mr-3">
                        <Building className="h-5 w-5" />
                      </div>
                      <CardTitle className="break-words">{workspace.workspace_name}</CardTitle>
                    </div>
                    <CardDescription>
                      ID: {workspace.workspace_id}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">API Quota:</span>
                        <span>{workspace.api_daily_quota} calls/day</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Content Quota:</span>
                        <span>{workspace.content_quota} experiments</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">API Key:</span>
                        <span className="font-mono">{workspace.api_key_first_characters}•••••</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Created:</span>
                        <span>{new Date(workspace.created_datetime_utc).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </CardContent>
                  <Separator />
                  <CardFooter className="flex justify-between pt-4">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={currentWorkspace?.workspace_id === workspace.workspace_id}
                      onClick={() => handleWorkspaceSwitch(workspace.workspace_name)}
                    >
                      Switch to
                    </Button>
                    <Link href={`/workspaces/${workspace.workspace_id}`}>
                      <Button size="sm" variant="ghost">
                        <Settings className="h-4 w-4 mr-2" />
                        Manage
                      </Button>
                    </Link>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="current">
            {currentWorkspace && (
              <div>
                <Card>
                  <CardHeader>
                    <div className="flex items-center">
                      <div className="p-2 bg-muted rounded-md mr-3">
                        <Building className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle>{currentWorkspace.workspace_name}</CardTitle>
                        <CardDescription>
                          Workspace ID: {currentWorkspace.workspace_id}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h3 className="text-md font-medium mb-2">Workspace Details</h3>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div className="text-muted-foreground">Created:</div>
                          <div>{new Date(currentWorkspace.created_datetime_utc).toLocaleDateString()}</div>

                          <div className="text-muted-foreground">Last Updated:</div>
                          <div>{new Date(currentWorkspace.updated_datetime_utc).toLocaleDateString()}</div>

                          <div className="text-muted-foreground">API Daily Quota:</div>
                          <div>{currentWorkspace.api_daily_quota} calls/day</div>

                          <div className="text-muted-foreground">Content Quota:</div>
                          <div>{currentWorkspace.content_quota} experiments</div>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-md font-medium mb-2">API Configuration</h3>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div className="text-muted-foreground">API Key Prefix:</div>
                          <div className="font-mono">{currentWorkspace.api_key_first_characters}•••••</div>

                          <div className="text-muted-foreground">Key Last Rotated:</div>
                          <div>{new Date(currentWorkspace.api_key_updated_datetime_utc).toLocaleDateString()}</div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                  <CardFooter className="flex justify-between pt-4 space-x-2">
                    <Button
                      onClick={() => router.push(`/workspaces/${currentWorkspace.workspace_id}`)}
                    >
                      <Settings className="h-4 w-4 mr-2" />
                      Manage Workspace
                    </Button>
                  </CardFooter>
                </Card>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      <CreateWorkspaceDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
      />
    </>
  );
}
