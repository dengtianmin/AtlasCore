export const siteConfig = {
  name: "AtlasCore",
  description: "面向知识系统的聊天、图谱与管理前端",
  adminNav: [
    { href: "/admin", label: "总览" },
    { href: "/admin/documents", label: "文档管理" },
    { href: "/admin/graph/sqlite-files", label: "SQLite 文件" },
    { href: "/admin/graph/md-files", label: "Markdown 文件" },
    { href: "/admin/graph/tasks", label: "抽取任务" },
    { href: "/admin/graph/prompt", label: "提取 Prompt" },
    { href: "/admin/graph/models", label: "提取模型" },
    { href: "/admin/review/rubric", label: "评分标准" },
    { href: "/admin/dify", label: "Dify 调试" },
    { href: "/admin/graph", label: "图管理" },
    { href: "/admin/logs", label: "问答日志" },
    { href: "/admin/exports", label: "导出管理" }
  ],
  publicNav: [
    { href: "/chat", label: "聊天" },
    { href: "/graph", label: "图谱" },
    { href: "/review", label: "评阅" },
    { href: "/admin/login", label: "管理员" }
  ]
};
