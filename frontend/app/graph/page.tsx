"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { PublicHeader } from "@/components/common/public-header";
import { GraphCanvas } from "@/components/graph/graph-canvas";
import { GraphFilters } from "@/components/graph/graph-filters";
import { GraphToolbar } from "@/components/graph/graph-toolbar";
import { NodeDetailPanel } from "@/components/graph/node-detail-panel";
import { getGraphOverview, getNodeDetails } from "@/lib/api/graph";

export default function GraphPage() {
  const [searchKeyword, setSearchKeyword] = useState("");
  const [labelFilter, setLabelFilter] = useState("");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [highlightPath, setHighlightPath] = useState<string[]>([]);
  const [expandDepth, setExpandDepth] = useState(1);

  const overviewQuery = useQuery({
    queryKey: ["graph-overview"],
    queryFn: () => getGraphOverview(120)
  });
  const nodeDetailsQuery = useQuery({
    queryKey: ["graph-node", selectedNodeId],
    queryFn: () => getNodeDetails(selectedNodeId!),
    enabled: Boolean(selectedNodeId)
  });

  const filteredGraph = useMemo(() => {
    const source = overviewQuery.data;
    if (!source) {
      return { nodes: [], edges: [] };
    }

    const normalizedKeyword = searchKeyword.trim().toLowerCase();
    const normalizedLabel = labelFilter.trim().toLowerCase();
    const nodes = source.nodes.filter((node) => {
      const content = `${String(node.properties.name ?? "")} ${JSON.stringify(node.properties)}`.toLowerCase();
      const matchesKeyword = !normalizedKeyword || content.includes(normalizedKeyword);
      const matchesLabel = !normalizedLabel || node.labels.some((label) => label.toLowerCase().includes(normalizedLabel));
      return matchesKeyword && matchesLabel;
    });

    const nodeIds = new Set(nodes.map((node) => node.id));
    return {
      nodes,
      edges: source.edges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
    };
  }, [labelFilter, overviewQuery.data, searchKeyword]);

  return (
    <div>
      <PublicHeader />
      <main className="mx-auto max-w-[1600px] px-6 py-10">
        <PageHeader
          title="图谱浏览"
          description="第一版以浏览为主，同时保留当前选中节点、搜索关键字、过滤条件、高亮路径与展开层级等状态结构，便于后续升级。"
        />
        {overviewQuery.isLoading ? <LoadingState label="正在加载图谱..." /> : null}
        {overviewQuery.isError ? <ErrorState message={(overviewQuery.error as Error).message} /> : null}
        {!overviewQuery.isLoading && !overviewQuery.isError ? (
          <div className="mt-6 grid gap-6 xl:grid-cols-[280px_1fr_320px]">
            <div className="space-y-4">
              <GraphToolbar
                search={searchKeyword}
                onSearchChange={(value) => {
                  setSearchKeyword(value);
                  setHighlightPath(value ? [value] : []);
                }}
                onReset={() => {
                  setSearchKeyword("");
                  setLabelFilter("");
                  setSelectedNodeId(null);
                  setHighlightPath([]);
                  setExpandDepth(1);
                }}
              />
              <GraphFilters labelFilter={labelFilter} onLabelFilterChange={setLabelFilter} />
              <div className="rounded-lg border bg-card p-4 text-sm text-muted-foreground">
                <p className="font-medium text-foreground">交互预留</p>
                <p className="mt-2">高亮路径：{highlightPath.length ? highlightPath.join(", ") : "未启用"}</p>
                <p className="mt-1">展开层级：{expandDepth}</p>
              </div>
            </div>

            <GraphCanvas nodes={filteredGraph.nodes} edges={filteredGraph.edges} onNodeClick={setSelectedNodeId} />

            <NodeDetailPanel node={nodeDetailsQuery.data?.node ?? null} />
          </div>
        ) : null}
      </main>
    </div>
  );
}
