import * as React from "react";
import { cn } from "../../lib/utils";

// shadcn/ui badge, one look, pointed at our colors

function Badge({ className, ...props }: React.ComponentProps<"span">) {
  return (
    <span
      data-slot="badge"
      className={cn(
        "inline-flex w-fit shrink-0 items-center rounded-full border border-brand/30 bg-brand-soft px-2.5 py-0.5 text-xs font-medium whitespace-nowrap text-brand",
        className,
      )}
      {...props}
    />
  );
}

export { Badge };
