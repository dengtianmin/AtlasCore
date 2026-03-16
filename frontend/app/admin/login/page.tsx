"use client";

import { useMutation } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { loginAdmin } from "@/lib/api/admin-auth";
import { setAdminToken } from "@/lib/auth/token";

const schema = z.object({
  username: z.string().min(3, "请输入用户名"),
  password: z.string().min(8, "密码长度至少为 8 位")
});

type FormValues = z.infer<typeof schema>;

export default function AdminLoginPage() {
  const router = useRouter();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      username: "admin",
      password: ""
    }
  });

  const loginMutation = useMutation({
    mutationFn: loginAdmin,
    onSuccess: (response) => {
      setAdminToken(response.access_token);
      router.replace("/admin");
      router.refresh();
    }
  });

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>管理员登录</CardTitle>
          <p className="text-sm text-muted-foreground">使用 AtlasCore 管理员账号进入后台。登录后可管理文档、日志和导出。</p>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={form.handleSubmit((values) => loginMutation.mutate(values))}>
            <div className="space-y-2">
              <label className="text-sm font-medium">用户名</label>
              <Input {...form.register("username")} />
              {form.formState.errors.username ? <p className="text-xs text-destructive">{form.formState.errors.username.message}</p> : null}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">密码</label>
              <Input type="password" {...form.register("password")} />
              {form.formState.errors.password ? <p className="text-xs text-destructive">{form.formState.errors.password.message}</p> : null}
            </div>
            {loginMutation.isError ? <p className="text-sm text-destructive">{(loginMutation.error as Error).message}</p> : null}
            <Button className="w-full" type="submit" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? "登录中..." : "进入后台"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
