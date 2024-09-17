"use client";

import React from "react";

import { MAB } from "../types";
import { PlusIcon } from "@heroicons/react/20/solid";
import { Link } from "@/components/catalyst/link";

export default function ExperimentCards({
  experiments,
}: {
  experiments: MAB[];
}) {
  return (
    <ul
      role="list"
      className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      {experiments.map((experiment) => (
        <li
          key={experiment.experiment_id}
          className="col-span-1 rounded-lg bg-white shadow min-h-40"
        >
          <div className="flex w-full items-center justify-between space-x-6 p-6">
            <div className="flex-1 truncate">
              <div className="flex items-center space-x-3 pb-4 justify-between">
                <h3 className="truncate text-sm font-medium text-gray-900">
                  {experiment.name}
                </h3>
                <div>
                  <span
                    className={`inline-flex flex-shrink-0 items-center rounded-full 
                    px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset mx-1
                    ${
                      experiment.isActive
                        ? "bg-green-50 text-green-700 ring-green-600/20"
                        : "bg-gray-50 text-gray-700 ring-gray-600/20"
                    }`}
                  >
                    {experiment.isActive ? "Active" : "Inactive"}
                  </span>

                  <span
                    className="inline-flex flex-shrink-0 items-center rounded-full 
                    px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset
                    bg-indigo-50 text-indigo-700 ring-indigo-600/20"
                  >
                    MAB
                  </span>
                </div>
              </div>
              <p className="mt-1 truncate text-sm text-gray-500 text-wrap">
                {experiment.description}
              </p>
            </div>
          </div>
          <div></div>
        </li>
      ))}

      {/* <!-- Add new item... --> */}
      <li
        key={"new"}
        className="col-span-1 rounded-lg bg-zinc-800 shadow border-2 border-dashed hover:border-solid
                  border-gray-400 min-h-40 transition ease-in-out "
      >
        <Link href="/experiments/add">
          <div
            className="transition ease-in-out duration-200
                        grid h-full items-center justify-items-center 
                        align-middle space-x-6 rounded-lg                       
                      p-6 hover:bg-zinc-700 active:bg-zinc-900"
          >
            <PlusIcon className="h-6 w-6 text-gray-400" aria-hidden="true" />
          </div>
        </Link>
      </li>
    </ul>
  );
}
