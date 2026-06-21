import React from "react";

import { severityToneClass } from "@/lib/statusStyles";

type Props = {
  severity?: string;
};

export default function SeverityBadge({ severity = "unknown" }: Props) {
  return (
    <span
      className={`rounded-full px-2 py-1 text-xs font-medium capitalize ${severityToneClass(
        severity,
      )}`}
    >
      {severity}
    </span>
  );
}
