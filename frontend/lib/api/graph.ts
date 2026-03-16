import { requestJson } from "@/lib/api/client";
import type { GraphNeighbors, GraphNodeDetails, GraphOverview } from "@/types/api";

export function getGraphOverview(limit = 100) {
  return requestJson<GraphOverview>(`/graph/overview?limit=${limit}`);
}

export function getNodeDetails(nodeId: string) {
  return requestJson<GraphNodeDetails>(`/graph/nodes/${nodeId}`);
}

export function getNodeNeighbors(nodeId: string, limit = 100) {
  return requestJson<GraphNeighbors>(`/graph/nodes/${nodeId}/neighbors?limit=${limit}`);
}
