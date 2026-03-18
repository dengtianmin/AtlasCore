"use client";

import { useState } from "react";
import { AlertTriangle, Bot, ChevronDown, ChevronUp, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn, formatDateTime } from "@/lib/utils";
import type { ReviewEvaluationResponse, ReviewItem, ReviewKeyIssue } from "@/types/api";

function getRiskTone(riskLevel?: string | null) {
  const normalized = riskLevel?.toLowerCase();
  if (normalized === "high") {
    return "border-red-200 bg-red-50 text-red-700";
  }
  if (normalized === "medium") {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }
  if (normalized === "low") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  return "border-slate-200 bg-slate-50 text-slate-600";
}

function getConclusionTone(conclusion: string) {
  if (conclusion.includes("不符合")) {
    return "text-red-700";
  }
  if (conclusion.includes("需复核")) {
    return "text-amber-700";
  }
  if (conclusion.includes("符合")) {
    return "text-emerald-700";
  }
  return "text-slate-700";
}

function ReviewItemRow({ item, defaultExpanded }: { item: ReviewItem; defaultExpanded: boolean }) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white/80 px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-slate-900">{item.item_name || "未命名条目"}</p>
            {item.conclusion ? <Badge className={cn("border-current bg-transparent", getConclusionTone(item.conclusion))}>{item.conclusion}</Badge> : null}
            {item.importance ? <Badge>{item.importance}</Badge> : null}
          </div>
          {item.scheme_excerpt ? <p className="text-sm leading-6 text-slate-600">方案摘录：{item.scheme_excerpt}</p> : null}
        </div>
        <Button variant="ghost" size="sm" className="shrink-0" onClick={() => setExpanded((current) => !current)}>
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </div>
      {expanded ? (
        <div className="mt-3 space-y-3 border-t border-dashed border-slate-200 pt-3 text-sm leading-6 text-slate-700">
          {item.standard_basis ? <p className="rounded-xl border-l-2 border-slate-300 bg-slate-50 px-3 py-2 text-slate-600">参考标准：{item.standard_basis}</p> : null}
          {item.reason ? <p>判定原因：{item.reason}</p> : null}
          {item.suggestion ? <p className="font-medium text-slate-900">修改建议：{item.suggestion}</p> : null}
        </div>
      ) : null}
    </div>
  );
}

function KeyIssueRow({ item }: { item: ReviewKeyIssue }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3">
      <div className="flex items-center gap-2">
        <ShieldAlert className="h-4 w-4 text-amber-600" />
        <p className="text-sm font-semibold text-slate-900">{item.title || "关键问题"}</p>
        {item.risk_level ? <Badge className={getRiskTone(item.risk_level)}>{item.risk_level}</Badge> : null}
      </div>
      {item.problem ? <p className="mt-2 text-sm leading-6 text-slate-700">{item.problem}</p> : null}
      {item.basis ? <p className="mt-2 text-xs leading-5 text-slate-500">依据：{item.basis}</p> : null}
      {item.suggestion ? <p className="mt-2 text-sm font-medium text-slate-900">建议：{item.suggestion}</p> : null}
    </div>
  );
}

export function ReviewMessageCard({ data, meta }: { data: ReviewEvaluationResponse; meta?: string | null }) {
  const defaultExpandedCount = 2;
  const [showAllItems, setShowAllItems] = useState(false);
  const visibleItems = showAllItems ? data.review_items : data.review_items.slice(0, defaultExpandedCount);

  return (
    <Card className="overflow-hidden border-slate-200 bg-white shadow-sm">
      <CardContent className="space-y-5 px-5 py-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-white">
              <Bot className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">评阅结果</p>
              <p className="text-xs text-slate-500">{formatDateTime(meta || data.created_at)}</p>
            </div>
          </div>
          <Badge className={getRiskTone(data.risk_level)}>
            {data.risk_level || "未标记风险"}
          </Badge>
        </div>

        <div className="grid gap-3 rounded-3xl border border-slate-200 bg-slate-50/80 p-4 md:grid-cols-3">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Score</p>
            <p className="mt-2 text-3xl font-semibold text-slate-950">{data.score ?? "未生成"}</p>
            {data.score === null ? <p className="mt-1 text-xs text-slate-500">本次未生成量化分数</p> : null}
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Grade</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">{data.grade || "未生成"}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Parse</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">{data.parse_status}</p>
          </div>
        </div>

        <section className="space-y-2">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">总体结论</p>
          <p className="text-sm leading-7 text-slate-800">{data.summary || "未返回总结。"}</p>
        </section>

        {visibleItems.length ? (
          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">审核详情</p>
              {data.review_items.length > defaultExpandedCount ? (
                <Button variant="ghost" size="sm" onClick={() => setShowAllItems((current) => !current)}>
                  {showAllItems ? "收起部分" : `展开全部 ${data.review_items.length} 项`}
                </Button>
              ) : null}
            </div>
            <div className="space-y-3">
              {visibleItems.map((item, index) => (
                <ReviewItemRow key={`${item.item_name}-${index}`} item={item} defaultExpanded={index < defaultExpandedCount} />
              ))}
            </div>
          </section>
        ) : null}

        {data.key_issues.length ? (
          <section className="space-y-3">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">关键问题</p>
            <div className="space-y-3">
              {data.key_issues.map((item, index) => (
                <KeyIssueRow key={`${item.title}-${index}`} item={item} />
              ))}
            </div>
          </section>
        ) : null}

        {data.deduction_logic.length ? (
          <section className="space-y-3">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">扣分依据</p>
            <div className="space-y-2">
              {data.deduction_logic.map((item, index) => (
                <div key={`${item.reason}-${index}`} className="flex items-start justify-between gap-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
                  <p className="leading-6 text-slate-700">{item.reason}</p>
                  <span className="shrink-0 font-semibold text-slate-900">-{item.deducted_score}</span>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {data.parse_status === "failed" && data.raw_text ? (
          <section className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              <p className="font-medium">结构化解析失败，以下为原始文本</p>
            </div>
            <p className="mt-2 whitespace-pre-wrap leading-6">{data.raw_text}</p>
          </section>
        ) : null}
      </CardContent>
    </Card>
  );
}
