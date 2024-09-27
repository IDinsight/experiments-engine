"use client";
import React from "react";
import EmptyPage from "./components/EmptyPage";
import { getAllMABExperiments } from "./api";
import { MAB } from "./types";
import ExperimentCard from "./components/ExperimentCard";
import Hourglass from "@/components/Hourglass";
import FloatingAddButton from "./components/FloatingAddButton";
import { Link } from "@/components/catalyst/link";
import { useAuth } from "@/utils/auth";

export default function Experiments() {
  const [experiments, setExperiments] = React.useState<MAB[]>([]);
  const [loading, setLoading] = React.useState(true);

  const { token } = useAuth();

  React.useEffect(() => {
    setLoading(true);
    getAllMABExperiments(token!).then((data) => {
      setExperiments(data);
    });
    setLoading(false);
  }, [token]);

  return loading ? (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="bg-white dark:bg-zinc-950 rounded-lg p-6 sm:p-8 md:p-10 flex flex-col items-center justify-center space-y-4 w-full max-w-sm mx-auto">
        <Hourglass />
        <span className="text-primary font-medium text-center">Loading...</span>
      </div>
    </div>
  ) : experiments.length > 0 ? (
    <div className="min-h-screen ">
      <ExperimentCardGrid experiments={experiments} />
      <Link href="/experiments/add">
        <FloatingAddButton />
      </Link>
    </div>
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
      className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 items-stretch"
    >
      {experiments.map((experiment) => (
        <li key={experiment.experiment_id}>
          <ExperimentCard experiment={experiment} />
        </li>
      ))}
    </ul>
  );
};
