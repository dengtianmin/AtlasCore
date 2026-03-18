"use client";

import { useMutation } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { loginUser } from "@/lib/api/user-auth";
import { setUserToken } from "@/lib/auth/token";

const schema = z.object({
  student_id: z.string().regex(/^\d{10}$/, "请输入 10 位学号"),
  password: z.string().min(1, "请输入密码")
});

type FormValues = z.infer<typeof schema>;

export default function UserLoginPage() {
  const router = useRouter();
  const [nextPath, setNextPath] = useState("/chat");
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      student_id: "",
      password: ""
    }
  });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setNextPath(params.get("next") || "/chat");
    form.setValue("student_id", params.get("student_id") || "");
  }, [form]);

  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (response) => {
      setUserToken(response.access_token);
      router.replace(nextPath);
      router.refresh();
    }
  });

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>学生登录</CardTitle>
          <p className="text-sm text-muted-foreground">登录后可使用聊天、图谱与评阅功能。</p>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={form.handleSubmit((values) => loginMutation.mutate(values))}>
            <div className="space-y-2">
              <label className="text-sm font-medium">学号</label>
              <Input {...form.register("student_id")} placeholder="10 位数字学号" />
              {form.formState.errors.student_id ? <p className="text-xs text-destructive">{form.formState.errors.student_id.message}</p> : null}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">密码</label>
              <Input type="password" {...form.register("password")} />
              {form.formState.errors.password ? <p className="text-xs text-destructive">{form.formState.errors.password.message}</p> : null}
            </div>
            {loginMutation.isError ? <p className="text-sm text-destructive">{(loginMutation.error as Error).message}</p> : null}
            <Button className="w-full" type="submit" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? "登录中..." : "登录"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            还没有账号？{" "}
            <Link href="/register" className="font-medium text-foreground underline underline-offset-4">
              去注册
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
