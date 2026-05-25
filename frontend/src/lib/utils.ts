export function formatPhone(raw: string | null | undefined): string {
  if (!raw) return "—";
  const digits = raw.replace(/\D/g, "");
  if (digits.length === 10) return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  if (digits.length === 11 && digits[0] === "1") return `(${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7)}`;
  return raw;
}

export function formatCurrency(value: string | number): string {
  const numberValue = typeof value === "string" ? Number(value) : value;

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(numberValue || 0);
}

export function formatNumber(value: string | number, digits = 2): string {
  const numberValue = typeof value === "string" ? Number(value) : value;
  return (numberValue || 0).toFixed(digits);
}