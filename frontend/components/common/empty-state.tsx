import { FileSearch } from "lucide-react";

import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  description,
  className
}: {
  title: string;
  description: string;
  className?: string;
}) {
  return (
    <div className={cn("flex min-h-[220px] flex-col items-center justify-center rounded-lg border border-dashed bg-card px-6 text-center", className)}>
      <FileSearch className="mb-4 h-8 w-8 text-muted-foreground" />
      <h3 className="text-base font-medium">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">{description}</p>
    </div>
  );
}
