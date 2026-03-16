"use client";

import { ThumbsDown, ThumbsUp } from "lucide-react";

import { Button } from "@/components/ui/button";

export function FeedbackActions({
  onLike,
  onDislike,
  disabled
}: {
  onLike: () => void;
  onDislike: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      <Button disabled={disabled} variant="ghost" size="sm" onClick={onLike}>
        <ThumbsUp className="mr-1 h-4 w-4" />
        有帮助
      </Button>
      <Button disabled={disabled} variant="ghost" size="sm" onClick={onDislike}>
        <ThumbsDown className="mr-1 h-4 w-4" />
        需改进
      </Button>
    </div>
  );
}
