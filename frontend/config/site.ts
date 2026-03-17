export const siteConfig = {
  name: "AtlasCore",
  description: "面向知识系统的聊天、图谱与管理前端",
  adminNav: [
    { href: "/admin", label: "总览" },
    { href: "/admin/documents", label: "文档管理" },
    { href: "/admin/dify", label: "Dify 调试" },
    { href: "/admin/graph", label: "图管理" },
    { href: "/admin/logs", label: "问答日志" },
    { href: "/admin/exports", label: "导出管理" }
  ],
  publicNav: [
    { href: "/chat", label: "聊天" },
    { href: "/graph", label: "图谱" },
    { href: "/admin/login", label: "管理员" }
  ]
};
