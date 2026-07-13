import { cn } from "@/lib/utils";
import { type ButtonHTMLAttributes, forwardRef } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

type ButtonSize = "sm" | "md" | "lg";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
};

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-primary text-primary-foreground shadow-sm hover:bg-primary-dark",
  secondary:
    "border border-border bg-surface text-text-secondary shadow-sm hover:bg-surface-secondary hover:text-text-primary",
  ghost: "text-text-secondary hover:bg-surface-secondary hover:text-text-primary",
  danger: "bg-error text-white shadow-sm hover:bg-error/90",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "rounded-md px-3 py-1.5 text-xs font-medium",
  md: "rounded-md px-4 py-2 text-sm font-semibold",
  lg: "rounded-lg px-6 py-2.5 text-sm font-semibold",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", disabled, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled}
      className={cn(
        "inline-flex items-center justify-center gap-2 transition-colors",
        variantStyles[variant],
        sizeStyles[size],
        disabled && "cursor-not-allowed opacity-50",
        className,
      )}
      {...props}
    />
  ),
);

Button.displayName = "Button";
