import React from "react";

export function DividerWithTitle({ title }: { title: string }) {
  return (
    <div className="bg-zinc-900 relative mt-8">
      <div aria-hidden="true" className="absolute inset-0 flex items-center">
        <div className="w-full border-t border-zinc-600" />
      </div>
      <div className="relative flex justify-start">
        <span className="bg-zinc-900 pr-3 text-base font-semibold leading-6 text-gray-200">
          {title}
        </span>
      </div>
    </div>
  );
}
