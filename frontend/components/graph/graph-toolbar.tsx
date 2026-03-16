import { RotateCcw } from "lucide-react";

import { SearchInput } from "@/components/common/search-input";
import { Button } from "@/components/ui/button";

export function GraphToolbar({
  search,
  onSearchChange,
  onReset
}: {
  search: string;
  onSearchChange: (value: string) => void;
  onReset: () => void;
}) {
  return (
    <div className="space-y-3 rounded-lg border bg-card p-4">
      <SearchInput placeholder="搜索节点名称或属性" value={search} onChange={(event) => onSearchChange(event.target.value)} />
      <Button variant="secondary" className="w-full justify-center" onClick={onReset}>
        <RotateCcw className="mr-2 h-4 w-4" />
        重置视图
      </Button>
    </div>
  );
}
