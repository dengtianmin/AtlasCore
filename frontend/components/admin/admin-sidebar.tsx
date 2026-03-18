"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutGrid, FileText, NotebookTabs, Download, Network, LogOut, FlaskConical, Database, Files, Settings2, Bot } from "lucide-react";

import { Button } from "@/components/ui/button";
import { siteConfig } from "@/config/site";
import { clearAdminToken } from "@/lib/auth/token";
import { cn } from "@/lib/utils";

const iconMap = {
  "/admin": LayoutGrid,
  "/admin/documents": FileText,
  "/admin/graph/sqlite-files": Database,
  "/admin/graph/md-files": Files,
  "/admin/graph/tasks": Network,
  "/admin/graph/prompt": Settings2,
  "/admin/graph/models": Bot,
  "/admin/review/rubric": Settings2,
  "/admin/review/logs": NotebookTabs,
  "/admin/dify": FlaskConical,
  "/admin/graph": Network,
  "/admin/logs": NotebookTabs,
  "/admin/exports": Download
};

export function AdminSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="flex min-h-screen w-64 flex-col border-r bg-white/90 p-4">
      <div className="border-b pb-4">
        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">AtlasCore</p>
        <h2 className="mt-2 text-lg font-semibold">管理员后台</h2>
      </div>
      <nav className="mt-4 flex-1 space-y-1">
        {siteConfig.adminNav.map((item) => {
          const Icon = iconMap[item.href as keyof typeof iconMap] ?? LayoutGrid;
          const active = item.href === "/admin" ? pathname === item.href : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                active && "bg-muted text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <Button
        variant="ghost"
        className="justify-start gap-2"
        onClick={() => {
          clearAdminToken();
          router.replace("/admin/login");
          router.refresh();
        }}
      >
        <LogOut className="h-4 w-4" />
        退出登录
      </Button>
    </aside>
  );
}
