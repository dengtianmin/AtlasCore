"use client";

import { useMutation } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { registerUser } from "@/lib/api/user-auth";

const schema = z.object({
  student_id: z.string().regex(/^\d{10}$/, "请输入 10 位学号"),
  name: z.string().regex(/^[\u4e00-\u9fff]+$/, "姓名需为纯汉字"),
  password: z.string().min(8, "密码长度至少为 8 位")
});

type FormValues = z.infer<typeof schema>;

export default function UserRegisterPage() {
  const router = useRouter();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      student_id: "",
      name: "",
      password: ""
    }
  });

  const registerMutation = useMutation({
    mutationFn: registerUser,
    onSuccess: (_response, variables) => {
      router.replace(`/login?student_id=${variables.student_id}`);
    }
  });

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>学生注册</CardTitle>
          <p className="text-sm text-muted-foreground">使用学号、姓名和密码创建普通用户账号。</p>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={form.handleSubmit((values) => registerMutation.mutate(values))}>
            <div className="space-y-2">
              <label className="text-sm font-medium">学号</label>
              <Input {...form.register("student_id")} placeholder="10 位数字学号" />
              {form.formState.errors.student_id ? <p className="text-xs text-destructive">{form.formState.errors.student_id.message}</p> : null}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">姓名</label>
              <Input {...form.register("name")} placeholder="纯汉字姓名" />
              {form.formState.errors.name ? <p className="text-xs text-destructive">{form.formState.errors.name.message}</p> : null}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">密码</label>
              <Input type="password" {...form.register("password")} />
              {form.formState.errors.password ? <p className="text-xs text-destructive">{form.formState.errors.password.message}</p> : null}
            </div>
            {registerMutation.isError ? <p className="text-sm text-destructive">{(registerMutation.error as Error).message}</p> : null}
            <Button className="w-full" type="submit" disabled={registerMutation.isPending}>
              {registerMutation.isPending ? "注册中..." : "注册"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            已有账号？{" "}
            <Link href="/login" className="font-medium text-foreground underline underline-offset-4">
              去登录
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
