import { Eye } from "lucide-react";

import { StatusBadge } from "@/components/common/status-badge";
import { Button } from "@/components/ui/button";
import { Table, TBody, TD, TH, THead } from "@/components/ui/table";
import { formatDateTime } from "@/lib/utils";
import type { AdminLogRecord } from "@/types/api";

export function LogTable({
  items,
  onView
}: {
  items: AdminLogRecord[];
  onView: (item: AdminLogRecord) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <THead>
          <tr>
            <TH>问题</TH>
            <TH>来源</TH>
            <TH>反馈</TH>
            <TH>时间</TH>
            <TH>操作</TH>
          </tr>
        </THead>
        <TBody>
          {items.map((item) => (
            <tr key={item.id}>
              <TD>
                <div className="max-w-xl">
                  <p className="font-medium">{item.question}</p>
                  <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{item.answer}</p>
                </div>
              </TD>
              <TD>
                <StatusBadge value={item.source} />
              </TD>
              <TD>
                <div className="space-y-1 text-xs">
                  <p>点赞：{item.feedback?.liked === null || item.feedback?.liked === undefined ? "未评价" : item.feedback.liked ? "是" : "否"}</p>
                  <p>评分：{item.feedback?.rating ?? "未评分"}</p>
                </div>
              </TD>
              <TD>{formatDateTime(item.created_at)}</TD>
              <TD>
                <Button variant="ghost" size="sm" onClick={() => onView(item)}>
                  <Eye className="mr-1 h-4 w-4" />
                  查看
                </Button>
              </TD>
            </tr>
          ))}
        </TBody>
      </Table>
    </div>
  );
}
