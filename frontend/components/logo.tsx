import { VidoraMark } from "@/components/vidora-mark";

export function Logo() {
  return (
    <div className="flex select-none items-center gap-2.5">
      <VidoraMark className="h-5 w-5 text-primary" />
      <span className="text-[13px] font-medium tracking-tight text-foreground/90">
        Vidora
      </span>
    </div>
  );
}
