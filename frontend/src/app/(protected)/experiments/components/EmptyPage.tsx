import { PlusIcon, BeakerIcon } from "@heroicons/react/20/solid";
import { Link } from "@/components/catalyst/link";
import React from "react";

export default function EmptyPage() {
  return (
    <div className="text-center">
      <BeakerIcon className="mx-auto h-12 w-12 text-gray-400" />

      <h3 className="mt-2 text-sm font-semibold text-gray-800 dark:text-gray-200">
        No experiments
      </h3>
      <p className="mt-1 text-sm dark:text-gray-400 text-gray-600">
        Get started by creating a new experiment.
      </p>
      <div className="mt-6">
        <Link
          href="/experiments/add"
          type="button"
          className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
        >
          <PlusIcon aria-hidden="true" className="-ml-0.5 mr-1.5 h-5 w-5" />
          New Experiment
        </Link>
      </div>
    </div>
  );
}
