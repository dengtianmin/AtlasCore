"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { LoadingState } from "@/components/common/loading-state";
import { getCurrentAdmin } from "@/lib/api/admin-auth";
import { getAdminToken } from "@/lib/auth/token";

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const token = getAdminToken();
  const meQuery = useQuery({
    queryKey: ["admin-me", token],
    queryFn: () => getCurrentAdmin(token),
    enabled: Boolean(token)
  });

  useEffect(() => {
    if (!token) {
      router.replace("/admin/login");
      return;
    }
    if (meQuery.isError) {
      router.replace("/admin/login");
    }
  }, [meQuery.isError, router, token]);

  if (!token || meQuery.isLoading) {
    return <LoadingState label="正在校验管理员身份..." />;
  }

  return <>{children}</>;
}
