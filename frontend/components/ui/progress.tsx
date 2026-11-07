"use client";

import * as ProgressPrimitive from "@radix-ui/react-progress";

import { cn } from "@/lib/utils";

export function Progress({
  value,
  className,
}: {
  value: number | null;
  className?: string;
}) {
  return (
    <ProgressPrimitive.Root
      value={value}
      className={cn(
        "relative h-1.5 w-full overflow-hidden rounded-full bg-secondary",
        className,
      )}
    >
      {value === null ? (
        <div className="h-full w-1/3 animate-[indeterminate_1.2s_ease-in-out_infinite] rounded-full bg-foreground/60" />
      ) : (
        <ProgressPrimitive.Indicator
          className="h-full w-full flex-1 rounded-full bg-foreground transition-transform duration-200 ease-out"
          style={{ transform: `translateX(-${100 - Math.min(100, Math.max(0, value))}%)` }}
        />
      )}
    </ProgressPrimitive.Root>
  );
}
