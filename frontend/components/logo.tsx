export function Logo() {
  return (
    <div className="flex select-none items-center gap-2.5">
      <img
        src="/vidora-icon.png"
        alt=""
        className="h-7 w-7 rounded-lg"
        width={28}
        height={28}
      />
      <span className="text-[13px] font-medium tracking-tight text-foreground/90">
        Vidora
      </span>
    </div>
  );
}
