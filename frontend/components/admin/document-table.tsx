import { Eye, RefreshCw, Trash2 } from "lucide-react";

import { StatusBadge } from "@/components/common/status-badge";
import { Button } from "@/components/ui/button";
import { Table, TBody, TD, TH, THead } from "@/components/ui/table";
import { formatDateTime, formatFileSize } from "@/lib/utils";
import type { DocumentRecord } from "@/types/api";

export function DocumentTable({
  items,
  onView,
  onDelete,
  onSyncGraph,
  onSyncDify
}: {
  items: DocumentRecord[];
  onView: (item: DocumentRecord) => void;
  onDelete: (item: DocumentRecord) => void;
  onSyncGraph: (item: DocumentRecord) => void;
  onSyncDify: (item: DocumentRecord) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <THead>
          <tr>
            <TH>文件</TH>
            <TH>状态</TH>
            <TH>上传时间</TH>
            <TH>大小</TH>
            <TH>同步</TH>
            <TH>操作</TH>
          </tr>
        </THead>
        <TBody>
          {items.map((item) => (
            <tr key={item.id}>
              <TD>
                <div>
                  <p className="font-medium">{item.filename}</p>
                  <p className="text-xs text-muted-foreground">{item.content_type ?? item.source_type}</p>
                </div>
              </TD>
              <TD>
                <StatusBadge value={item.status} />
              </TD>
              <TD>{formatDateTime(item.uploaded_at)}</TD>
              <TD>{formatFileSize(item.file_size)}</TD>
              <TD>
                <div className="space-y-1 text-xs">
                  <p>图谱：{item.synced_to_graph ? "已同步" : "未同步"}</p>
                  <p>Dify：{item.synced_to_dify ? "已同步" : "未同步"}</p>
                </div>
              </TD>
              <TD>
                <div className="flex flex-wrap gap-2">
                  <Button variant="ghost" size="sm" onClick={() => onView(item)}>
                    <Eye className="mr-1 h-4 w-4" />
                    详情
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => onSyncGraph(item)}>
                    <RefreshCw className="mr-1 h-4 w-4" />
                    图谱
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => onSyncDify(item)}>
                    <RefreshCw className="mr-1 h-4 w-4" />
                    Dify
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => onDelete(item)}>
                    <Trash2 className="mr-1 h-4 w-4" />
                    删除
                  </Button>
                </div>
              </TD>
            </tr>
          ))}
        </TBody>
      </Table>
    </div>
  );
}
