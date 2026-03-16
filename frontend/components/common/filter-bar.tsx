export function FilterBar({ children }: { children: React.ReactNode }) {
  return <div className="grid gap-3 rounded-lg border bg-card p-4 md:grid-cols-2 xl:grid-cols-5">{children}</div>;
}
