import * as React from "react";

import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "flex min-h-[96px] w-full rounded-md border bg-white px-3 py-2 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:border-primary/60",
          className
        )}
        {...props}
      />
    );
  }
);

Textarea.displayName = "Textarea";
