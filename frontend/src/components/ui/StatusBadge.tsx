import React from "react";

type Props = {
  status: string;
};

const styles: Record<string, string> = {
  delivered: "bg-green-100 text-green-700",
  in_transit: "bg-blue-100 text-blue-700",
  booked: "bg-yellow-100 text-yellow-700",
  cancelled: "bg-red-100 text-red-700",
};

export default function StatusBadge({ status }: Props) {
  const normalizedStatus = status.toLowerCase();

  return (
    <span
      className={`rounded-full px-2 py-1 text-xs font-semibold capitalize ${
        styles[normalizedStatus] ?? "bg-slate-100 text-slate-700"
      }`}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}