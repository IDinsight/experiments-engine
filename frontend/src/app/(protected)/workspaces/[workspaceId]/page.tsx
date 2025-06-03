"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/utils/auth";
import { apiCalls } from "@/utils/api";
import { useToast } from "@/hooks/use-toast";

import { Building, ChevronLeftIcon, Users, Key, Copy, History } from "lucide-react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Hourglass from "@/components/Hourglass";
import { Separator } from "@/components/ui/separator";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Workspace, WorkspaceUser, ApiKeyRotation } from "../types";

export default function WorkspaceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user: currentUser, token, currentWorkspace, fetchWorkspaces, switchWorkspace } =
    useAuth();

  const { toast } = useToast();

  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [workspaceUsers, setWorkspaceUsers] = useState<WorkspaceUser[]>([]);
  const [keyRotationHistory, setKeyRotationHistory] = useState<ApiKeyRotation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isRotatingKey, setIsRotatingKey] = useState(false);
  const [newApiKey, setNewApiKey] = useState<string | null>(null);
  const [isApiKeyDialogOpen, setIsApiKeyDialogOpen] = useState(false);
  const [isCurrentUserAdmin, setIsCurrentUserAdmin] = useState(false);

  const workspaceId = Number(params.workspaceId);

  useEffect(() => {
    const loadWorkspaceData = async () => {
      if (!token) return;

      setIsLoading(true);
      try {
        // Fetch workspace details
        const workspaceData = await apiCalls.getWorkspaceById(
          token,
          workspaceId
        );
        setWorkspace(workspaceData);

        // Fetch workspace users
        const usersData = await apiCalls.getWorkspaceUsers(token, workspaceId);
        setWorkspaceUsers(usersData);

        // Check if current user is admin
        const currentUserData = usersData.find((user: WorkspaceUser) => user.username === currentUser);
        setIsCurrentUserAdmin(currentUserData?.role === "admin");

        await loadKeyRotationHistory();
      } catch (error) {
        console.error("Error loading workspace data:", error);
        toast({
          title: "Error",
          description: "Failed to load workspace details",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadWorkspaceData();
  }, [token, workspaceId, currentUser, toast]);

  const loadKeyRotationHistory = async () => {
    if (!token) return;

    setIsLoadingHistory(true);
    try {
      const historyData = await apiCalls.getWorkspaceKeyHistory(token, workspaceId);
      setKeyRotationHistory(historyData);
    } catch (error) {
      console.error("Error loading key rotation history:", error);
      toast({
        title: "Error",
        description: "Failed to load key rotation history",
        variant: "destructive",
      });
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleRotateApiKey = async () => {
    if (!token || !workspace) return;

    setIsRotatingKey(true);
    try {
      // Need to switch to this workspace first if it's not the current one
      if (currentWorkspace?.workspace_id !== workspaceId) {
        await switchWorkspace(workspace.workspace_name);
      }

      const result = await apiCalls.rotateWorkspaceApiKey(token);
      setNewApiKey(result.new_api_key);
      setIsApiKeyDialogOpen(true);

      // Refresh workspaces data
      await fetchWorkspaces();

      // Refresh workspace details
      const updatedWorkspace = await apiCalls.getWorkspaceById(
        token,
        workspaceId
      );
      setWorkspace(updatedWorkspace);

      await loadKeyRotationHistory();

      toast({
        title: "Success",
        description: "API key rotated successfully",
        variant: "success",
      });
    } catch (error: Error | unknown) {
      const errorMessage = error instanceof Error ? error.message : "Failed to rotate API key";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsRotatingKey(false);
    }
  };

  const handleCopyApiKey = () => {
    if (!newApiKey) return;

    navigator.clipboard.writeText(newApiKey);
    toast({
      title: "Copied",
      description: "API key copied to clipboard",
    });
  };

  const handleRemoveUser = async (username: string) => {
    if (!token) return;

    try {
      await apiCalls.removeUserFromWorkspace(token, workspaceId, username);

      // Refresh user list
      const updatedUsers = await apiCalls.getWorkspaceUsers(token, workspaceId);
      setWorkspaceUsers(updatedUsers);

      toast({
        title: "Success",
        description: `${username} has been removed from the workspace`,
        variant: "success",
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "Failed to remove user";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="rounded-lg bg-card p-6 flex flex-col items-center justify-center space-y-4 w-full max-w-sm mx-auto">
          <Hourglass />
          <span className="text-primary font-medium text-center">
            Loading workspace details...
          </span>
        </div>
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="text-center">
          <h2 className="text-2xl font-bold">Workspace Not Found</h2>
          <p className="text-muted-foreground">
            The requested workspace could not be found
          </p>
          <Button className="mt-4" onClick={() => router.push("/workspaces")}>
            <ChevronLeftIcon className="mr-2 h-4 w-4" />
            Back to Workspaces
          </Button>
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
                <BreadcrumbLink href="/workspaces">Workspaces</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>{workspace.workspace_name}</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>

        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center">
            <div className="p-2 bg-muted rounded-md mr-3">
              <Building className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                {workspace.workspace_name}
              </h1>
              <p className="text-muted-foreground">
                Workspace ID: {workspace.workspace_id}
              </p>
            </div>
          </div>
          <Button variant="outline" onClick={() => router.push("/workspaces")}>
            <ChevronLeftIcon className="mr-2 h-4 w-4" />
            Back to Workspaces
          </Button>
        </div>

        <Tabs defaultValue="overview">
          <TabsList className="mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="api">API</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <Card>
              <CardHeader>
                <CardTitle>Workspace Overview</CardTitle>
                <CardDescription>
                  Summary information about this workspace
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-md font-medium mb-2">
                      Workspace Details
                    </h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="text-muted-foreground">Name:</div>
                      <div>{workspace.workspace_name}</div>

                      <div className="text-muted-foreground">ID:</div>
                      <div>{workspace.workspace_id}</div>

                      <div className="text-muted-foreground">Created:</div>
                      <div>
                        {new Date(
                          workspace.created_datetime_utc
                        ).toLocaleDateString()}
                      </div>

                      <div className="text-muted-foreground">Last Updated:</div>
                      <div>
                        {new Date(
                          workspace.updated_datetime_utc
                        ).toLocaleDateString()}
                      </div>

                      <div className="text-muted-foreground">
                        API Daily Quota:
                      </div>
                      <div>{workspace.api_daily_quota} calls/day</div>

                      <div className="text-muted-foreground">
                        Content Quota:
                      </div>
                      <div>{workspace.content_quota} experiments</div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-md font-medium mb-2">
                      API Configuration
                    </h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="text-muted-foreground">
                        API Key Prefix:
                      </div>
                      <div className="font-mono">
                        {workspace.api_key_first_characters}•••••
                      </div>

                      <div className="text-muted-foreground">
                        Key Last Rotated:
                      </div>
                      <div>
                        {new Date(
                          workspace.api_key_updated_datetime_utc
                        ).toLocaleDateString()}
                        {workspace.api_key_rotated_by_username && (
                          <span> by <span className="font-medium">{workspace.api_key_rotated_by_username}</span></span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
              {currentWorkspace?.workspace_id !== workspace.workspace_id && (
                <CardFooter className="flex justify-end pt-4">
                  <Button
                    onClick={async () => {
                      try {
                        setIsLoading(true);
                        await switchWorkspace(workspace.workspace_name);
                        toast({
                          title: "Success",
                          description: `Switched to ${workspace.workspace_name} workspace`,
                        });
                      } catch (error) {
                        console.error("Error switching workspace:", error);
                        toast({
                          title: "Error",
                          description: "Failed to switch workspace",
                          variant: "destructive",
                        });
                      } finally {
                        setIsLoading(false);
                      }
                    }}
                  >
                    Switch to this workspace
                  </Button>
                </CardFooter>
              )}
            </Card>
          </TabsContent>

          <TabsContent value="users">
            <Card>
              <CardHeader>
                <CardTitle className="flex justify-between items-center">
                  <span>Workspace Users</span>
                  {isCurrentUserAdmin && !workspace.is_default && (
                    <Button
                      size="sm"
                      onClick={() =>
                        router.push(`/workspaces/${workspaceId}/users/invite`)
                      }
                    >
                      <Users className="h-4 w-4 mr-2" />
                      Invite User
                    </Button>
                  )}
                </CardTitle>
                <CardDescription>
                  {workspace.is_default
                    ? "This is a default workspace. User management is restricted."
                    : "Manage users who have access to this workspace"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {workspaceUsers.length === 0 ? (
                  <div className="text-center py-8">
                    <Users className="mx-auto h-12 w-12 text-muted-foreground opacity-50" />
                    <h3 className="mt-2 text-lg font-medium">No users found</h3>
                    <p className="text-sm text-muted-foreground">
                      {workspace.is_default
                        ? "Default workspaces automatically include all users."
                        : isCurrentUserAdmin
                          ? "Invite users to collaborate in this workspace"
                          : null}
                    </p>
                  </div>
                ) : (
                  <div className="border rounded-md">
                    <div className="grid grid-cols-12 gap-4 p-4 bg-muted font-medium">
                      <div className="col-span-4">User</div>
                      <div className="col-span-3">Role</div>
                      <div className="col-span-3">Joined</div>
                      <div className="col-span-2">Actions</div>
                    </div>
                    {workspaceUsers.map((user) => (
                      <div
                        key={user.user_id}
                        className="grid grid-cols-12 gap-4 p-4 border-t"
                      >
                        <div className="col-span-4 flex items-center">
                          <div className="font-medium">
                            {user.first_name} {user.last_name}
                          </div>
                          <div className="ml-2 text-sm text-muted-foreground">
                            {user.username}
                          </div>
                        </div>
                        <div className="col-span-3 capitalize">
                          {user.role.toLowerCase()}
                          {user.is_default_workspace && (
                            <span className="ml-2 text-xs bg-muted px-2 py-1 rounded-full">
                              Default
                            </span>
                          )}
                        </div>
                        <div className="col-span-3 text-sm text-muted-foreground">
                          {new Date(
                            user.created_datetime_utc
                          ).toLocaleDateString()}
                        </div>
                        <div className="col-span-2">
                          {isCurrentUserAdmin && (
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="text-red-500 border-red-200 hover:bg-red-50 hover:text-red-600"
                                >
                                  Remove
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>
                                    Remove user?
                                  </AlertDialogTitle>
                                  <AlertDialogDescription>
                                    Are you sure you want to remove{" "}
                                    {user.first_name} {user.last_name} from
                                    this workspace?
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>
                                    Cancel
                                  </AlertDialogCancel>
                                  <AlertDialogAction
                                    className="bg-red-600 hover:bg-red-700"
                                    onClick={() =>
                                      handleRemoveUser(user.username)
                                    }
                                  >
                                    Remove
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="api">
            <Card>
              <CardHeader>
                <CardTitle className="flex justify-between items-center">
                  <span>API Configuration</span>
                  {isCurrentUserAdmin && (
                    <Button
                      size="sm"
                      onClick={handleRotateApiKey}
                      disabled={isRotatingKey}
                    >
                      <Key className="h-4 w-4 mr-2" />
                      {isRotatingKey ? "Rotating..." : "Rotate API Key"}
                    </Button>
                  )}
                </CardTitle>
                <CardDescription>
                  Manage API settings for this workspace
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <h3 className="text-lg font-medium">Current API Key</h3>
                  <div className="bg-muted p-4 rounded-md font-mono">
                    {workspace.api_key_first_characters}
                    •••••••••••••••••••••••••••
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Last updated on{" "}
                    {new Date(
                      workspace.api_key_updated_datetime_utc
                    ).toLocaleString()}
                    {workspace.api_key_rotated_by_username && (
                      <span> by <span className="font-medium">{workspace.api_key_rotated_by_username}</span></span>
                    )}
                  </p>
                </div>

                <div className="space-y-2">
                  <h3 className="text-lg font-medium">API Usage Limits</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-muted rounded-md">
                      <div className="text-sm text-muted-foreground">
                        Daily Quota
                      </div>
                      <div className="text-2xl font-bold">
                        {workspace.api_daily_quota}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        API calls per day
                      </div>
                    </div>
                    <div className="p-4 bg-muted rounded-md">
                      <div className="text-sm text-muted-foreground">
                        Content Quota
                      </div>
                      <div className="text-2xl font-bold">
                        {workspace.content_quota}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Experiments
                      </div>
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="space-y-2">
                  <h3 className="text-lg font-medium flex items-center">
                    <History className="h-4 w-4 mr-2" />
                    API Key Rotation History
                  </h3>
                  <div className="border rounded-md">
                    <div className="grid grid-cols-12 gap-4 p-4 bg-muted font-medium">
                      <div className="col-span-5">Date & Time</div>
                      <div className="col-span-4">Rotated By</div>
                      <div className="col-span-3">Key Prefix</div>
                    </div>
                    {isLoadingHistory ? (
                      <div className="p-8 text-center">
                        <Hourglass />
                        <p className="mt-2 text-sm text-muted-foreground">Loading history...</p>
                      </div>
                    ) : keyRotationHistory.length > 0 ? (
                      keyRotationHistory.map((rotation) => (
                        <div key={rotation.rotation_id} className="grid grid-cols-12 gap-4 p-4 border-t">
                          <div className="col-span-5 text-sm">
                            {new Date(rotation.rotation_datetime_utc).toLocaleString()}
                          </div>
                          <div className="col-span-4 text-sm">
                            {rotation.rotated_by_username}
                          </div>
                          <div className="col-span-3 text-sm font-mono">
                            {rotation.key_first_characters}•••••
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="p-4 text-center text-sm text-muted-foreground">
                        No rotation history available
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground italic">
                    This table shows the complete history of API key rotations.
                  </p>
                </div>

                <Separator />

                {isCurrentUserAdmin && (
                  <div className="p-4 border border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-900/20 rounded-md">
                    <h4 className="text-md font-medium text-amber-800 dark:text-amber-400">
                      About API Key Rotation
                    </h4>
                    <p className="text-sm text-amber-700 dark:text-amber-300 mt-2">
                      When you rotate your API key, the old key will be
                      immediately invalidated. Any services or applications using
                      the old key will need to be updated with the new key. Make
                      sure to copy and save your new key as it will only be shown
                      once.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Dialog for showing the new API key */}
      <Dialog open={isApiKeyDialogOpen} onOpenChange={setIsApiKeyDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New API Key Generated</DialogTitle>
            <DialogDescription>
              Make sure to copy your new API key. You won't be able to see it
              again!
            </DialogDescription>
          </DialogHeader>

          <div className="p-4 bg-muted rounded-md font-mono text-sm overflow-x-auto">
            {newApiKey}
          </div>

          <DialogFooter className="flex justify-between">
            <Button variant="outline" onClick={handleCopyApiKey}>
              <Copy className="h-4 w-4 mr-2" />
              Copy to Clipboard
            </Button>
            <Button onClick={() => setIsApiKeyDialogOpen(false)}>
              I've Saved My Key
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
