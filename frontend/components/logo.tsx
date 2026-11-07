import { ArrowDown } from "lucide-react";

export function Logo() {
  return (
    <div className="flex select-none items-center gap-2.5">
      <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/80 bg-card">
        <ArrowDown className="h-3.5 w-3.5" strokeWidth={1.8} />
      </span>
      <span className="text-[13px] font-medium tracking-tight text-foreground/90">
        Local YT-DLP
      </span>
    </div>
  );
}
