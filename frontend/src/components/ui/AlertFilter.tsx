import React from "react";
type Props = {
  value?: string;
  onChange?: (value: string) => void;
};

export default function AlertFilter({ value = "all", onChange }: Props) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <label className="mr-3 text-sm font-medium text-slate-700">
        Severity
      </label>
      <select
        value={value}
        onChange={(event) => onChange?.(event.target.value)}
        className="rounded-md border border-slate-300 px-3 py-2 text-sm"
      >
        <option value="all">All</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>
    </div>
  );
}