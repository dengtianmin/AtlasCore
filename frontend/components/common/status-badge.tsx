import { Badge } from "@/components/ui/badge";

const variants: Record<string, "neutral" | "success" | "warning" | "destructive" | "accent"> = {
  ok: "success",
  uploaded: "accent",
  indexed: "success",
  graph_pending: "warning",
  graph_synced: "success",
  failed: "destructive",
  true: "success",
  false: "neutral"
};

export function StatusBadge({ value }: { value: string | boolean | null | undefined }) {
  const text = value === null || value === undefined ? "未记录" : String(value);
  return <Badge variant={variants[text] ?? "neutral"}>{text}</Badge>;
}
