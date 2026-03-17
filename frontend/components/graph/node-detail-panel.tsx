import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { GraphNodeDetails } from "@/types/api";

export function NodeDetailPanel({
  details,
  isLoading = false,
  errorMessage,
  onNodeSelect
}: {
  details?: GraphNodeDetails | null;
  isLoading?: boolean;
  errorMessage?: string | null;
  onNodeSelect?: (nodeId: string) => void;
}) {
  if (errorMessage) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>实体详情</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-6 text-destructive">{errorMessage}</CardContent>
      </Card>
    );
  }

  if (isLoading && !details) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>实体详情</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-6 text-muted-foreground">正在加载实体详情...</CardContent>
      </Card>
    );
  }

  if (!details?.node) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>实体详情</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-6 text-muted-foreground">
          点击画布中的节点后，在这里查看名称、描述、来源文档和一跳相关实体。
        </CardContent>
      </Card>
    );
  }

  const node = details.node;
  const sourceDocuments = details.source_documents ?? [];
  const relatedEntities = details.related_entities ?? [];

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{String(node.properties.name ?? node.id)}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">实体类型</p>
          <p className="mt-1 leading-6">{node.labels.join(" / ") || "未标注"}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">实体描述</p>
          <p className="mt-1 leading-6 text-foreground/90">{details.description?.trim() || "暂无描述"}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">来源文档</p>
          {sourceDocuments.length ? (
            <ul className="mt-2 space-y-2">
              {sourceDocuments.map((item) => (
                <li key={`${item.document_id ?? "fallback"}-${item.title}`} className="rounded-md border bg-muted/30 px-3 py-2">
                  <p className="font-medium text-foreground">{item.title}</p>
                  <p className="mt-1 break-all text-xs text-muted-foreground">
                    {item.document_id ? `ID: ${item.document_id}` : "未关联业务文档 ID"}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 leading-6 text-muted-foreground">暂无来源文档</p>
          )}
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">相关实体</p>
          {relatedEntities.length ? (
            <div className="mt-2 flex flex-wrap gap-2">
              {relatedEntities.map((item) => (
                <Button key={item.id} variant="ghost" size="sm" className="h-auto border px-3 py-2 text-left" onClick={() => onNodeSelect?.(item.id)}>
                  <span>{item.name}</span>
                </Button>
              ))}
            </div>
          ) : (
            <p className="mt-1 leading-6 text-muted-foreground">暂无相关实体</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
