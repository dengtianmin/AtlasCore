import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function DataTableShell({
  title,
  description,
  children,
  actions
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
        </div>
        {actions}
      </CardHeader>
      <CardContent className="p-0">{children}</CardContent>
    </Card>
  );
}
