import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Table, TBody, TD, TH, THead } from "@/components/ui/table";
import { formatDateTime } from "@/lib/utils";
import type { ExportRecord } from "@/types/api";

export function ExportTable({
  items,
  onDownload
}: {
  items: ExportRecord[];
  onDownload: (item: ExportRecord) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <THead>
          <tr>
            <TH>文件名</TH>
            <TH>导出类型</TH>
            <TH>记录数</TH>
            <TH>操作者</TH>
            <TH>时间</TH>
            <TH>下载</TH>
          </tr>
        </THead>
        <TBody>
          {items.map((item) => (
            <tr key={item.export_id}>
              <TD className="font-medium">{item.filename}</TD>
              <TD>{item.export_type}</TD>
              <TD>{item.record_count}</TD>
              <TD>{item.operator}</TD>
              <TD>{formatDateTime(item.export_time)}</TD>
              <TD>
                <Button variant="ghost" size="sm" onClick={() => onDownload(item)}>
                  <Download className="mr-1 h-4 w-4" />
                  下载 CSV
                </Button>
              </TD>
            </tr>
          ))}
        </TBody>
      </Table>
    </div>
  );
}
