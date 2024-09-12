import React from "react";
import EmptyPage from "./components/EmptyPage";

export default function Experiments() {
  return (
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
