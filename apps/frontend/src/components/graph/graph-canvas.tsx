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
} from "@/entities/ontology/types";

type Selection =
  | { kind: "node"; node: GraphNodeViewModel }
  | { kind: "edge"; edge: GraphEdgeViewModel }
  | null;

export function GraphCanvas({
  nodes,
  edges,
  onSelect,
  onNodeRename,
  onEdgeRename,
}: {
  nodes: GraphNodeViewModel[];
  edges: GraphEdgeViewModel[];
  onSelect?: (selection: Selection) => void;
  onNodeRename?: (node: GraphNodeViewModel) => void;
  onEdgeRename?: (edge: GraphEdgeViewModel) => void;
}) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);

  useEffect(() => {
    if (!hostRef.current) return;

    const cy = cytoscape({
      container: hostRef.current,
      elements: [
        ...nodes.map((n) => ({
          data: {
            id: n.id,
            label: n.name,
            type: n.entityType,
            color: colorForType(n.entityType),
            ref: n,
          },
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
            "background-color": "data(color)",
            label: "data(label)",
            color: "#10231d",
            "font-size": 11,
            "font-weight": 600,
            "text-wrap": "wrap",
            "text-max-width": "120px",
            "text-valign": "bottom",
            "text-margin-y": 8,
            width: 34,
            height: 34,
            "border-width": 2,
            "border-color": "#f8fafc",
            "overlay-padding": 8,
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-width": 4,
            "border-color": "#10231d",
            opacity: 1,
          },
        },
        {
          selector: "edge",
          style: {
            "line-color": "#6b8f87",
            "target-arrow-color": "#6b8f87",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": 9,
            color: "#37534d",
            "text-rotation": "autorotate",
            "text-background-color": "#f8fafc",
            "text-background-opacity": 0.95,
            "text-background-padding": "3px",
            width: 2,
            "overlay-padding": 6,
          },
        },
        {
          selector: "edge:selected",
          style: {
            "line-color": "#10231d",
            "target-arrow-color": "#10231d",
            width: 3,
          },
        },
      ],
      layout: { name: "cose", animate: false, padding: 60, idealEdgeLength: 140 },
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
    cy.on("dbltap", "node", (evt) => {
      const node = evt.target as NodeSingular;
      const ref = node.data("ref") as GraphNodeViewModel;
      onNodeRename?.(ref);
    });
    cy.on("dbltap", "edge", (evt) => {
      const edge = evt.target as EdgeSingular;
      const ref = edge.data("ref") as GraphEdgeViewModel;
      onEdgeRename?.(ref);
    });

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [nodes, edges, onEdgeRename, onNodeRename, onSelect]);

  return <div ref={hostRef} className="h-full min-h-[400px] w-full" />;
}

function colorForType(entityType: string) {
  const palette = ["#3bb273", "#4a90e2", "#ff9f1c", "#e76f51", "#8d6cab", "#2a9d8f"];
  const seed = entityType
    .split("")
    .reduce((total, char) => total + char.charCodeAt(0), 0);
  return palette[seed % palette.length];
}
