"use client";

import { useEffect, useRef } from "react";
import cytoscape, {
  type Core,
  type EdgeSingular,
  type NodeSingular,
} from "cytoscape";
import type {
  GraphEdgeViewModel,
  GraphNodeViewModel,
} from "@/src/entities/ontology/types";

type Selection =
  | { kind: "node"; node: GraphNodeViewModel }
  | { kind: "edge"; edge: GraphEdgeViewModel }
  | null;

export function GraphCanvas({
  nodes,
  edges,
  onSelect,
}: {
  nodes: GraphNodeViewModel[];
  edges: GraphEdgeViewModel[];
  onSelect?: (selection: Selection) => void;
}) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);

  useEffect(() => {
    if (!hostRef.current) return;

    const cy = cytoscape({
      container: hostRef.current,
      elements: [
        ...nodes.map((n) => ({
          data: { id: n.id, label: n.name, type: n.entityType, ref: n },
        })),
        ...edges
          .filter((e) => nodes.some((n) => n.id === e.sourceId))
          .filter((e) => nodes.some((n) => n.id === e.targetId))
          .map((e) => ({
            data: {
              id: e.id,
              source: e.sourceId,
              target: e.targetId,
              label: e.relationType,
              ref: e,
            },
          })),
      ],
      style: [
        {
          selector: "node",
          style: {
            "background-color": "#2563eb",
            label: "data(label)",
            color: "#111",
            "font-size": 10,
            "text-wrap": "wrap",
            "text-max-width": "90px",
            "text-valign": "bottom",
            "text-margin-y": 4,
            width: 22,
            height: 22,
          },
        },
        {
          selector: "node:selected",
          style: {
            "background-color": "#f59e0b",
            "border-width": 2,
            "border-color": "#f59e0b",
          },
        },
        {
          selector: "edge",
          style: {
            "line-color": "#94a3b8",
            "target-arrow-color": "#94a3b8",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": 8,
            color: "#475569",
            "text-rotation": "autorotate",
            "text-background-color": "#ffffff",
            "text-background-opacity": 0.9,
            "text-background-padding": "2px",
            width: 1.2,
          },
        },
        {
          selector: "edge:selected",
          style: {
            "line-color": "#f59e0b",
            "target-arrow-color": "#f59e0b",
            width: 2,
          },
        },
      ],
      layout: { name: "cose", animate: false, padding: 40 },
      wheelSensitivity: 0.2,
    });

    cy.on("tap", "node", (evt) => {
      const node = evt.target as NodeSingular;
      const ref = node.data("ref") as GraphNodeViewModel;
      onSelect?.({ kind: "node", node: ref });
    });
    cy.on("tap", "edge", (evt) => {
      const edge = evt.target as EdgeSingular;
      const ref = edge.data("ref") as GraphEdgeViewModel;
      onSelect?.({ kind: "edge", edge: ref });
    });
    cy.on("tap", (evt) => {
      if (evt.target === cy) onSelect?.(null);
    });

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [nodes, edges, onSelect]);

  return <div ref={hostRef} className="h-full min-h-[400px] w-full" />;
}
