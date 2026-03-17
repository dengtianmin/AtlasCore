import ReactMarkdown from "react-markdown";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatDateTime } from "@/lib/utils";

export function ChatMessageCard({
  role,
  content,
  meta,
  source,
  status,
  providerMessageId,
  workflowRunId
}: {
  role: "user" | "assistant";
  content: string;
  meta?: string;
  source?: string;
  status?: string;
  providerMessageId?: string | null;
  workflowRunId?: string | null;
}) {
  const statusVariant =
    status === "succeeded" ? "success" : status === "failed" ? "destructive" : status === "processing" ? "warning" : "neutral";

  return (
    <Card className={role === "assistant" ? "bg-white" : "bg-muted/40"}>
      <CardContent className="space-y-3 px-5 py-4">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{role === "assistant" ? "AtlasCore" : "用户提问"}</span>
          {meta ? <span>{formatDateTime(meta)}</span> : null}
        </div>
        {role === "assistant" ? (
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <Badge variant="accent">{source || "atlascore"}</Badge>
            {status ? <Badge variant={statusVariant}>{status}</Badge> : null}
          </div>
        ) : null}
        {role === "assistant" ? (
          <div className="prose-atlascore">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm leading-7">{content}</p>
        )}
        {role === "assistant" && (providerMessageId || workflowRunId) ? (
          <div className="space-y-1 text-xs text-muted-foreground">
            {providerMessageId ? <p>provider_message_id: {providerMessageId}</p> : null}
            {workflowRunId ? <p>workflow_run_id: {workflowRunId}</p> : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
