import React from "react";

import { Info } from "lucide-react";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface MethodCardProps {
  title: string;
  description: string;
  infoTitle: string;
  infoDescription: string;
  selected: boolean;
  disabled?: boolean;
  onClick: () => void;
}

export function MethodCard({
  title,
  description,
  infoTitle,
  infoDescription,
  selected,
  disabled = false,
  onClick,
}: MethodCardProps) {
  // Helper function to conditionally join classNames
  const classNames = (...classes: (string | boolean | undefined)[]) => {
    return classes.filter(Boolean).join(" ");
  };

  return (
    <div
      className={classNames(
        "relative flex flex-col p-4 rounded-lg border-2 transition-all h-full",
        selected
          ? "border-primary bg-accent shadow-md "
          : "border-secondary bg-card",
        disabled
          ? "opacity-60 cursor-not-allowed"
          : "cursor-pointer hover:border-border "
      )}
      onClick={disabled ? undefined : onClick}
      aria-checked={selected}
      role="radio"
      aria-disabled={disabled}
      tabIndex={disabled ? -1 : 0}
      onKeyDown={(e) => {
        if ((e.key === "Enter" || e.key === " ") && !disabled) {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <Dialog>
        <DialogTrigger asChild>
          <button
            className="absolute top-2 right-2 text-muted-foreground hover:text-primary"
            onClick={(e) => e.stopPropagation()}
            aria-label={`More information about ${title}`}
            disabled={disabled}
          >
            <Info className="h-5 w-5" />
          </button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{infoTitle}</DialogTitle>
            <DialogDescription>{infoDescription}</DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>

      <div className="flex-1">
        <h3
          className={classNames(
            "text-lg font-medium mb-2 ",
            disabled && "text-zinc-500"
          )}
        >
          {title}
          {disabled && <span className="ml-1 ">[Coming soon]</span>}
        </h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
