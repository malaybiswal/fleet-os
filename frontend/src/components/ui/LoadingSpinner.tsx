export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-6">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />
    </div>
  );
}