export function LoadingState({ label = "加载中..." }: { label?: string }) {
  return (
    <div className="flex min-h-[180px] items-center justify-center rounded-lg border bg-card text-sm text-muted-foreground">
      {label}
    </div>
  );
}
