import React from "react";

import { statusToneClass } from "@/lib/statusStyles";

type Props = {
  status: string;
};

export default function StatusBadge({ status }: Props) {
  return (
    <span
      className={`rounded-full px-2 py-1 text-xs font-semibold capitalize ${statusToneClass(
        status,
      )}`}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}
