import React from "react";

export function DividerWithTitle({ title }: { title: string }) {
  return (
    <div className="dark:bg-zinc-900 bg-white relative mt-8">
      <div aria-hidden="true" className="absolute inset-0 flex items-center">
        <div className="w-full border-t dark:border-zinc-600 border-zinc-300" />
      </div>
      <div className="relative flex justify-start">
        <span className="dark:bg-zinc-900 bg-white pr-3 text-base font-semibold leading-6 dark:text-gray-200 text-gray-800">
          {title}
        </span>
      </div>
    </div>
  );
}
