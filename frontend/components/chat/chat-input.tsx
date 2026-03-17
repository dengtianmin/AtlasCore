"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const schema = z.object({
  question: z.string().min(1, "请输入问题").max(4000, "问题长度过长")
});

type FormValues = z.infer<typeof schema>;

export function ChatInput({
  onSubmit,
  isPending
}: {
  onSubmit: (value: string) => Promise<boolean> | boolean;
  isPending: boolean;
}) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      question: ""
    }
  });

  return (
    <form
      className="space-y-3"
      onSubmit={form.handleSubmit(async (values) => {
        const submitted = await onSubmit(values.question);
        if (submitted) {
          form.reset();
        }
      })}
    >
      <Textarea placeholder="输入你的问题，系统会通过 AtlasCore 统一聊天接口处理。" {...form.register("question")} />
      {form.formState.errors.question ? (
        <p className="text-xs text-destructive">{form.formState.errors.question.message}</p>
      ) : null}
      <div className="flex justify-end">
        <Button disabled={isPending} type="submit">
          {isPending ? "发送中..." : "发送问题"}
        </Button>
      </div>
    </form>
  );
}
