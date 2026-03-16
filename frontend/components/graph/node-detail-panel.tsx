import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function NodeDetailPanel({
  node
}: {
  node?: {
    id: string;
    labels: string[];
    properties: Record<string, unknown>;
  } | null;
}) {
  if (!node) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>节点详情</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-6 text-muted-foreground">点击画布中的节点后，在这里查看标签、属性和值。</CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{String(node.properties.name ?? node.id)}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">标签</p>
          <p className="mt-1 leading-6">{node.labels.join(" / ") || "未标注"}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">属性</p>
          <dl className="mt-2 space-y-2">
            {Object.entries(node.properties).map(([key, value]) => (
              <div key={key} className="grid grid-cols-[96px_1fr] gap-2">
                <dt className="text-muted-foreground">{key}</dt>
                <dd className="break-all">{String(value)}</dd>
              </div>
            ))}
          </dl>
        </div>
      </CardContent>
    </Card>
  );
}
