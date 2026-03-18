"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { siteConfig } from "@/config/site";
import { clearUserToken, getUserToken } from "@/lib/auth/token";
import { cn } from "@/lib/utils";

export function PublicHeader() {
  const pathname = usePathname();
  const hasUserToken = Boolean(getUserToken());

  return (
    <header className="border-b bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div>
          <Link href="/chat" className="text-lg font-semibold tracking-tight">
            {siteConfig.name}
          </Link>
          <p className="text-xs text-muted-foreground">{siteConfig.description}</p>
        </div>
        <nav className="flex items-center gap-2">
          {siteConfig.publicNav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                pathname === item.href && "bg-muted text-foreground"
              )}
            >
              {item.label}
            </Link>
          ))}
          {hasUserToken ? (
            <button
              type="button"
              className="rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              onClick={() => {
                clearUserToken();
                window.location.href = "/login";
              }}
            >
              退出登录
            </button>
          ) : (
            <>
              <Link
                href="/login"
                className={cn(
                  "rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                  pathname === "/login" && "bg-muted text-foreground"
                )}
              >
                登录
              </Link>
              <Link
                href="/register"
                className={cn(
                  "rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                  pathname === "/register" && "bg-muted text-foreground"
                )}
              >
                注册
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
