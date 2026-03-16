"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";

import { EmptyState } from "@/components/common/empty-state";
import type { GraphEdge, GraphNode } from "@/types/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false
});

type GraphCanvasProps = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick: (nodeId: string) => void;
};

export function GraphCanvas({ nodes, edges, onNodeClick }: GraphCanvasProps) {
  const graphData = useMemo(
    () => ({
      nodes: nodes.map((node) => ({
        id: node.id,
        name: String(node.properties.name ?? node.id),
        labels: node.labels
      })),
      links: edges.map((edge) => ({
        source: edge.source,
        target: edge.target,
        id: edge.id,
        label: edge.type
      }))
    }),
    [edges, nodes]
  );

  if (!nodes.length) {
    return <EmptyState title="暂无图谱数据" description="当前没有可展示的节点。请检查图 SQLite 数据是否已导入，或等待图运行层重载。" className="h-full" />;
  }

  return (
    <div className="h-[720px] rounded-lg border bg-card">
      <ForceGraph2D
        graphData={graphData}
        nodeLabel={(node: any) => `${String(node.name)} (${Array.isArray(node.labels) ? node.labels.join(", ") : ""})`}
        linkLabel={(link: any) => String(link.label ?? "")}
        backgroundColor="rgba(255,255,255,0)"
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const label = String(node.name);
          const fontSize = 12 / globalScale;
          ctx.font = `${fontSize}px sans-serif`;
          ctx.fillStyle = "#3a5876";
          ctx.beginPath();
          ctx.arc(node.x ?? 0, node.y ?? 0, 6, 0, 2 * Math.PI, false);
          ctx.fill();
          ctx.fillStyle = "#233143";
          ctx.fillText(label, (node.x ?? 0) + 10, (node.y ?? 0) + 4);
        }}
        onNodeClick={(node: any) => onNodeClick(String(node.id))}
        linkDirectionalParticles={1}
        linkDirectionalParticleWidth={1.5}
      />
    </div>
  );
}
