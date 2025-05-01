import { PlusIcon, FlaskConical, TriangleAlert } from "lucide-react";
import Link from "next/link";
import React from "react";

export default function EmptyPage({ loadingError }: { loadingError: string }) {
  return (
    <div>
      {loadingError !== "" ? (
        <div className="text-center">
          <TriangleAlert className="mx-auto h-12 w-12 text-destructive" />
          <h3 className="mt-2 text-sm font-semibold text-destructive">
            {loadingError}
          </h3>
        </div>
      ) : (
        <div className="text-center">
          <FlaskConical className="mx-auto h-12 w-12 text-gray-400" />

          <h3 className="mt-2 text-sm font-semibold text-foreground">
            No experiments
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Get started by creating a new experiment.
          </p>
          <div className="mt-6">
            <Link
              href="/experiments/add"
              type="button"
              className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-xs hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              <PlusIcon aria-hidden="true" className="-ml-0.5 mr-1.5 h-5 w-5" />
              New Experiment
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
