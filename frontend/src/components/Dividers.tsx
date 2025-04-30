import React from "react";

export function DividerWithTitle({ title }: { title: string }) {
  return (
    <div className="relative mt-8 mb-4">
      <div aria-hidden="true" className="absolute inset-0 flex items-center">
        <div className="w-full border-t " />
      </div>
      <div className="relative flex justify-start">
        <span className="bg-background pr-3 text-base font-semibold leading-6 ">
          {title}
        </span>
      </div>
    </div>
  );
}
