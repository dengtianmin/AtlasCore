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
  selectedNodeId?: string | null;
  relatedNodeIds?: string[];
  onNodeClick: (nodeId: string) => void;
};

export function GraphCanvas({ nodes, edges, selectedNodeId = null, relatedNodeIds = [], onNodeClick }: GraphCanvasProps) {
  const relatedNodeIdSet = useMemo(() => new Set(relatedNodeIds), [relatedNodeIds]);
  const hasSelection = Boolean(selectedNodeId);
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
        linkColor={(link: any) => {
          const touchesSelection = selectedNodeId && (link.source?.id === selectedNodeId || link.target?.id === selectedNodeId);
          if (touchesSelection) {
            return "#b96a16";
          }
          return hasSelection ? "rgba(35, 49, 67, 0.14)" : "rgba(58, 88, 118, 0.22)";
        }}
        linkWidth={(link: any) => {
          const touchesSelection = selectedNodeId && (link.source?.id === selectedNodeId || link.target?.id === selectedNodeId);
          return touchesSelection ? 2.2 : 1;
        }}
        linkDirectionalParticles={(link: any) => {
          const touchesSelection = selectedNodeId && (link.source?.id === selectedNodeId || link.target?.id === selectedNodeId);
          return touchesSelection ? 2 : hasSelection ? 0 : 1;
        }}
        linkDirectionalParticleWidth={(link: any) => {
          const touchesSelection = selectedNodeId && (link.source?.id === selectedNodeId || link.target?.id === selectedNodeId);
          return touchesSelection ? 2.2 : 1.5;
        }}
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const label = String(node.name);
          const fontSize = 12 / globalScale;
          const isSelected = node.id === selectedNodeId;
          const isRelated = !isSelected && relatedNodeIdSet.has(String(node.id));
          const isDimmed = hasSelection && !isSelected && !isRelated;
          const radius = isSelected ? 8.5 : isRelated ? 7 : 6;
          const fillStyle = isSelected
            ? "#b96a16"
            : isRelated
              ? "#4f7d73"
              : isDimmed
                ? "rgba(58, 88, 118, 0.45)"
                : "#3a5876";
          const textStyle = isDimmed ? "rgba(35, 49, 67, 0.55)" : "#233143";
          ctx.font = `${fontSize}px sans-serif`;
          ctx.fillStyle = fillStyle;
          ctx.beginPath();
          ctx.arc(node.x ?? 0, node.y ?? 0, radius, 0, 2 * Math.PI, false);
          ctx.fill();
          if (isSelected) {
            ctx.strokeStyle = "rgba(185, 106, 22, 0.25)";
            ctx.lineWidth = 4 / globalScale;
            ctx.stroke();
          }
          ctx.fillStyle = textStyle;
          ctx.fillText(label, (node.x ?? 0) + radius + 4, (node.y ?? 0) + 4);
        }}
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x ?? 0, node.y ?? 0, 10, 0, 2 * Math.PI, false);
          ctx.fill();
        }}
        onNodeClick={(node: any) => onNodeClick(String(node.id))}
      />
    </div>
  );
}
