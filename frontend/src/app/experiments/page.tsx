"use client";
import React from "react";
import EmptyPage from "./components/EmptyPage";
import { getAllMABExperiments } from "./api";
import { MAB } from "./types";
import ExperimentCard from "./components/ExperimentCard";

export default function Experiments() {
  const [experiments, setExperiments] = React.useState<MAB[]>([]);

  React.useEffect(() => {
    getAllMABExperiments().then((data) => {
      setExperiments(data);
    });
  }, []);

  return experiments.length > 0 ? (
    <ExperimentCardGrid experiments={experiments} />
  ) : (
    <div
      className="grid grow grid-rows-1 items-center justify-items-center sm:p-20 "
      style={{ minHeight: "calc(100vh - 200px)" }}
    >
      <main className="flex flex-col gap-8 row-start-1 items-center sm:items-start">
        <span className="content-center grow">
          <EmptyPage />
        </span>
      </main>
    </div>
  );
}

const ExperimentCardGrid = ({ experiments }: { experiments: MAB[] }) => {
  return (
    <ul
      role="list"
      className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      {experiments.map((experiment) => (
        <li key={experiment.experiment_id}>
          <ExperimentCard experiment={experiment} />
        </li>
      ))}
    </ul>
  );
};
