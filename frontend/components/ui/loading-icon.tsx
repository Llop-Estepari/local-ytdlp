"use client";

import { useEffect, useRef } from "react";
import { LoaderCircleIcon, type LoaderCircleIconHandle } from "lucide-animated";

import { cn } from "@/lib/utils";

interface LoadingIconProps {
  size?: number;
  className?: string;
}

/**
 * Animated loading indicator.
 *
 * lucide-animated icons animate on hover by default; this wrapper starts the
 * continuous spin while the component is mounted instead.
 */
export function LoadingIcon({ size = 16, className }: LoadingIconProps) {
  const ref = useRef<LoaderCircleIconHandle>(null);

  useEffect(() => {
    ref.current?.startAnimation();
    return () => ref.current?.stopAnimation();
  }, []);

  return (
    <LoaderCircleIcon
      ref={ref}
      size={size}
      animateOnHover={false}
      aria-hidden="true"
      className={cn("inline-flex shrink-0", className)}
    />
  );
}
