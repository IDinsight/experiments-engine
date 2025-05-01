"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { KeyRound, Copy } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/utils/auth";
import { useEffect } from "react";
import Hourglass from "@/components/Hourglass";
import { getUser, rotateAPIKey } from "../api";

export function ApiKeyDisplay() {
  const { token } = useAuth();

  const [apiKey, setApiKey] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newKey, setNewKey] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const { toast } = useToast();

  useEffect(() => {
    setIsLoading(true);
    getUser(token)
      .then((data) => {
        setApiKey(data.api_key_first_characters);
      })
      .catch((error: Error) => {
        console.log(error);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [token]);

  const handleGenerateKey = async () => {
    setIsRefreshing(true);
    rotateAPIKey(token)
      .then((data) => {
        setNewKey(data.new_api_key);
        setIsModalOpen(true);
      })
      .catch((error: Error) => {
        console.log(error);
        toast({
          title: "Error",
          description: "Failed to generate new API key",
          variant: "destructive",
        });
      })
      .finally(() => {
        setIsRefreshing(false);
      });
  };

  const handleCopyKey = async () => {
    try {
      await navigator.clipboard.writeText(newKey);
      toast({
        title: "Copied!",
        description: "API key copied to clipboard",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to copy API key",
        variant: "destructive",
      });
    }
  };

  const handleConfirm = () => {
    setApiKey(newKey);
    setIsModalOpen(false);
    toast({
      title: "Success",
      description: "API key has been updated",
    });
  };

  return isLoading ? (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="bg-white dark:bg-zinc-950 rounded-lg p-6 sm:p-8 md:p-10 flex flex-col items-center justify-center space-y-4 w-full max-w-sm mx-auto">
        <Hourglass />
        <span className="text-primary font-medium text-center">Loading...</span>
      </div>
    </div>
  ) : (
    <div className="space-y-4">
      <div className="flex items-center justify-between p-4 border flex-wrap gap-4 rounded-lg bg-muted">
        <div className="flex items-center gap-2 truncate">
          <KeyRound className="w-4 h-4 text-muted-foreground" />
          <span className="font-mono ">
            {apiKey.slice(0, 5)}
            {"•".repeat(27)}
          </span>
        </div>
        <Button onClick={handleGenerateKey} disabled={isRefreshing}>
          {isRefreshing ? "Generating..." : "Recreate Key"}
        </Button>
      </div>

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogTitle>New API Key Generated</DialogTitle>
          <DialogDescription>
            Make sure to copy your new API key. You won&apos;t be able to see it
            again!
          </DialogDescription>
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg font-mono break-all">
              {newKey}
            </div>
            <div className="flex items-center justify-between mt-4">
              <Button variant="outline" onClick={handleCopyKey}>
                <Copy className="w-4 h-4 mr-2" />
                Copy
              </Button>
              <Button onClick={handleConfirm}>
                I&apos;ve saved my API key
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
