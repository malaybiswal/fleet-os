import React from "react";
type Props = {
  severity?: string;
};

const severityStyles: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-green-100 text-green-700",
};

export default function SeverityBadge({ severity = "unknown" }: Props) {
  const normalizedSeverity = severity.toLowerCase();
  const className =
    severityStyles[normalizedSeverity] ?? "bg-slate-100 text-slate-700";

  return (
    <span
      className={`rounded-full px-2 py-1 text-xs font-medium capitalize ${className}`}
    >
      {severity}
    </span>
  );
}