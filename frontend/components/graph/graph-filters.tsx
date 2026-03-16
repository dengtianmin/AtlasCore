import { Input } from "@/components/ui/input";

export function GraphFilters({
  labelFilter,
  onLabelFilterChange
}: {
  labelFilter: string;
  onLabelFilterChange: (value: string) => void;
}) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="mb-3 text-sm font-medium">基础过滤</p>
      <Input
        placeholder="按标签过滤，如 Entity"
        value={labelFilter}
        onChange={(event) => onLabelFilterChange(event.target.value)}
      />
      <p className="mt-2 text-xs leading-5 text-muted-foreground">后续可继续扩展路径高亮、展开层级和属性过滤。</p>
    </div>
  );
}
