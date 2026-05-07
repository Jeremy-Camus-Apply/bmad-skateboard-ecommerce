"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm text-sm font-medium ring-offset-surface transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-primary focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-accent text-text-primary hover:bg-accent/90",
        destructive: "bg-error text-text-primary hover:bg-error/90",
        outline:
          "border border-border bg-surface hover:bg-surface-elevated hover:text-text-primary",
        ghost: "hover:bg-surface-elevated hover:text-text-primary",
        link: "text-accent underline-offset-4 hover:underline min-h-11 min-w-11",
      },
      size: {
        default: "h-10 px-4 py-2 min-h-11",
        sm: "h-9 rounded-sm px-3 min-h-11",
        lg: "h-11 rounded-sm px-8",
        icon: "h-10 w-10 min-h-11 min-w-11",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
