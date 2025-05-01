"use client";

import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import MABChart from "./components/MABChart";
import MABArmsProgress from "./components/MABArmsProgress";
import NotificationDetails from "./components/Notifications";
import ExtraInfo from "./components/ExtraInfo";

import { getMABExperimentById } from "../api";
import { useParams } from "next/navigation";
import { useAuth } from "@/utils/auth";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

import {
  MABExperimentDetails,
  MABArmDetails,
  Notification,
  ExtraInfo as ExtraInfoType,
} from "./types";

export default function ExperimentDetails() {
  const { experimentId } = useParams();
  const [armsDetails, setArmsDetails] = useState<MABArmDetails[]>([]);
  const [experimentDetails, setExperimentDetails] =
    useState<MABExperimentDetails | null>(null);
  const [notificationData, setNotificationData] = useState<Notification[]>([]);
  const [extraInfo, setExtraInfo] = useState<ExtraInfoType | null>(null);

  const { token } = useAuth();

  const experimentType = "Multi-armed Bandit";

  useEffect(() => {
    if (!token) return;
    getMABExperimentById(token, Number(experimentId)).then((data) => {
      setArmsDetails(data.arms);
      setExperimentDetails(data);
      setNotificationData(data.notifications);
      setExtraInfo({
        dateCreated: data.created_datetime_utc,
        lastTrialDate: data.last_trial_datetime_utc,
        experimentType: experimentType,
        nTrials: data.n_trials,
      });
    });
  }, [experimentId, token]);

  return (
    <div className="container mx-auto p-6">
      <Breadcrumb className="mb-4 w-full">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/experiments">Experiments</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator>/</BreadcrumbSeparator>
          <BreadcrumbItem>
            <BreadcrumbPage>
              {experimentDetails
                ? `#${experimentDetails?.experiment_id}: ${experimentDetails?.name}`
                : "Experiment Details"}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-semibold dark:text-gray-100">
            {experimentDetails ? experimentDetails?.name : "Experiment Details"}
          </h1>
          <p className="text-muted-foreground dark:text-gray-400">
            {experimentDetails ? experimentDetails.description : "Loading..."}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge
            variant={experimentDetails?.is_active ? "default" : "destructive"}
            className={
              experimentDetails?.is_active
                ? "bg-green-500 hover:bg-green-600"
                : ""
            }
          >
            {experimentDetails?.is_active ? "Active" : "Inactive"}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left column - Chart and Arms */}
        <div className="md:col-span-2 space-y-6">
          <MABChart experimentData={experimentDetails} />
          <MABArmsProgress armsData={armsDetails} />
        </div>

        {/* Right column - Experiment Details */}
        <div className="space-y-6">
          <NotificationDetails
            notificationData={notificationData}
            dateCreated={
              experimentDetails ? experimentDetails.created_datetime_utc : null
            }
            nTrials={experimentDetails ? experimentDetails.n_trials : null}
          />
          <ExtraInfo data={extraInfo} />
        </div>
      </div>
    </div>
  );
}
