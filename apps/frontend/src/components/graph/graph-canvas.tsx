"use client";

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
} from "react";
import { useTheme } from "next-themes";
import cytoscape, {
  type Core,
  type EdgeSingular,
  type NodeSingular,
} from "cytoscape";
import type {
  GraphEdgeViewModel,
  GraphNodeViewModel,
} from "@/entities/ontology/types";

export type GraphCanvasHandle = {
  zoomIn: () => void;
  zoomOut: () => void;
  fit: () => void;
  centerOn: (nodeId: string) => void;
};

type Selection =
  | { kind: "node"; node: GraphNodeViewModel }
  | { kind: "edge"; edge: GraphEdgeViewModel }
  | null;

function readCssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const raw = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  if (!raw) return fallback;
  return raw.startsWith("#") || raw.startsWith("rgb") ? raw : fallback;
}

type GraphCanvasProps = {
  nodes: GraphNodeViewModel[];
  edges: GraphEdgeViewModel[];
  onSelect?: (selection: Selection) => void;
  onNodeRename?: (node: GraphNodeViewModel) => void;
  onEdgeRename?: (edge: GraphEdgeViewModel) => void;
};

export const GraphCanvas = forwardRef<GraphCanvasHandle, GraphCanvasProps>(
  function GraphCanvas(
    { nodes, edges, onSelect, onNodeRename, onEdgeRename },
    ref,
  ) {
    const hostRef = useRef<HTMLDivElement | null>(null);
    const cyRef = useRef<Core | null>(null);
    const { resolvedTheme } = useTheme();

    const palette = useMemo(() => {
      void resolvedTheme;
      const primary = readCssVar("--primary", "#3b82f6");
      const secondary = readCssVar("--secondary", "#64748b");
      const accent = readCssVar("--accent", "#8b5cf6");
      const ring = readCssVar("--ring", "#0ea5e9");
      const muted = readCssVar("--muted-foreground", "#78716c");
      const chart = readCssVar("--chart-3", "#f97316");
      return [primary, secondary, accent, ring, chart, muted];
    }, [resolvedTheme]);

    useImperativeHandle(ref, () => ({
      zoomIn: () => {
        const cy = cyRef.current;
        if (!cy) return;
        cy.zoom(Math.min(cy.zoom() * 1.2, 4));
      },
      zoomOut: () => {
        const cy = cyRef.current;
        if (!cy) return;
        cy.zoom(Math.max(cy.zoom() / 1.2, 0.08));
      },
      fit: () => {
        cyRef.current?.fit(undefined, 60);
      },
      centerOn: (nodeId: string) => {
        const cy = cyRef.current;
        if (!cy) return;
        const node = cy.nodes().filter((n) => n.id() === nodeId);
        if (node.nonempty()) {
          cy.animate({ fit: { eles: node, padding: 80 }, duration: 200 });
        }
      },
    }));

    useEffect(() => {
      if (!hostRef.current) return;

      const layoutName = nodes.length > 200 ? "circle" : "cose";

      const cy = cytoscape({
        container: hostRef.current,
        elements: [
          ...nodes.map((n) => ({
            data: {
              id: n.id,
              label: n.name,
              type: n.entityType,
              color: colorForType(n.entityType, palette),
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
              color: readCssVar("--foreground", "#0f172a"),
              "font-size": 11,
              "font-weight": 600,
              "text-wrap": "wrap",
              "text-max-width": "120px",
              "text-valign": "bottom",
              "text-margin-y": 8,
              width: 34,
              height: 34,
              "border-width": 2,
              "border-color": readCssVar("--background", "#f8fafc"),
              "overlay-padding": 8,
            },
          },
          {
            selector: "node:selected",
            style: {
              "border-width": 4,
              "border-color": readCssVar("--primary", "#10231d"),
              opacity: 1,
            },
          },
          {
            selector: "edge",
            style: {
              "line-color": readCssVar("--muted-foreground", "#6b8f87"),
              "target-arrow-color": readCssVar("--muted-foreground", "#6b8f87"),
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              label: "data(label)",
              "font-size": 9,
              color: readCssVar("--foreground", "#37534d"),
              "text-rotation": "autorotate",
              "text-background-color": readCssVar("--background", "#f8fafc"),
              "text-background-opacity": 0.95,
              "text-background-padding": "3px",
              width: 2,
              "overlay-padding": 6,
            },
          },
          {
            selector: "edge:selected",
            style: {
              "line-color": readCssVar("--primary", "#10231d"),
              "target-arrow-color": readCssVar("--primary", "#10231d"),
              width: 3,
            },
          },
        ],
        layout: {
          name: layoutName,
          animate: false,
          padding: 60,
          ...(layoutName === "cose" ? { idealEdgeLength: 140 } : {}),
        },
        wheelSensitivity: 0.2,
      });

      cy.on("tap", "node", (evt) => {
        const node = evt.target as NodeSingular;
        const refNode = node.data("ref") as GraphNodeViewModel;
        onSelect?.({ kind: "node", node: refNode });
      });
      cy.on("tap", "edge", (evt) => {
        const edge = evt.target as EdgeSingular;
        const refEdge = edge.data("ref") as GraphEdgeViewModel;
        onSelect?.({ kind: "edge", edge: refEdge });
      });
      cy.on("tap", (evt) => {
        if (evt.target === cy) onSelect?.(null);
      });
      cy.on("dbltap", "node", (evt) => {
        const node = evt.target as NodeSingular;
        const refNode = node.data("ref") as GraphNodeViewModel;
        onNodeRename?.(refNode);
      });
      cy.on("dbltap", "edge", (evt) => {
        const edge = evt.target as EdgeSingular;
        const refEdge = edge.data("ref") as GraphEdgeViewModel;
        onEdgeRename?.(refEdge);
      });

      cyRef.current = cy;
      return () => {
        cy.destroy();
        cyRef.current = null;
      };
    }, [nodes, edges, onEdgeRename, onNodeRename, onSelect, palette]);

    return <div ref={hostRef} className="h-full min-h-0 w-full" />;
  },
);

function colorForType(entityType: string, palette: string[]) {
  const seed = entityType
    .split("")
    .reduce((total, char) => total + char.charCodeAt(0), 0);
  return palette[seed % palette.length] ?? palette[0];
}
