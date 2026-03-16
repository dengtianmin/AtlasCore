import ReactMarkdown from "react-markdown";

import { Card, CardContent } from "@/components/ui/card";
import { formatDateTime } from "@/lib/utils";

export function ChatMessageCard({
  role,
  content,
  meta
}: {
  role: "user" | "assistant";
  content: string;
  meta?: string;
}) {
  return (
    <Card className={role === "assistant" ? "bg-white" : "bg-muted/40"}>
      <CardContent className="space-y-3 px-5 py-4">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{role === "assistant" ? "AtlasCore" : "用户提问"}</span>
          {meta ? <span>{formatDateTime(meta)}</span> : null}
        </div>
        {role === "assistant" ? (
          <div className="prose-atlascore">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm leading-7">{content}</p>
        )}
      </CardContent>
    </Card>
  );
}
