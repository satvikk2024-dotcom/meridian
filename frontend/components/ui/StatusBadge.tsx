"use client";

export type BadgeStatus = "pending" | "planning" | "running" | "complete" | "failed";

const STATUS_CONFIG: Record<
  BadgeStatus,
  { dotClass: string; labelClass: string; label: string }
> = {
  pending: {
    dotClass: "bg-fg-muted",
    labelClass: "text-fg-muted",
    label: "Pending",
  },
  planning: {
    dotClass: "bg-warning animate-pulse-warning",
    labelClass: "text-warning",
    label: "Planning",
  },
  running: {
    dotClass: "bg-accent animate-pulse-accent",
    labelClass: "text-accent",
    label: "Running",
  },
  complete: {
    dotClass: "bg-accent",
    labelClass: "text-accent",
    label: "Complete",
  },
  failed: {
    dotClass: "bg-danger",
    labelClass: "text-danger",
    label: "Failed",
  },
};

interface StatusBadgeProps {
  status: BadgeStatus;
  label?: string; // override default label
  className?: string;
}

export default function StatusBadge({ status, label, className = "" }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <span className={`block h-[6px] w-[6px] rounded-full flex-shrink-0 ${config.dotClass}`} />
      <span className={`font-mono text-micro tracking-wide ${config.labelClass}`}>
        {label ?? config.label}
      </span>
    </span>
  );
}
