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