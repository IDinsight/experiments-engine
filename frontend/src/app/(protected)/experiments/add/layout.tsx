import React from "react";
import { ExperimentProvider } from "./components/AddExperimentContext";
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <ExperimentProvider>{children}</ExperimentProvider>;
}
