"use client";

import { useMemo, useState } from "react";
import {
  DndContext,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  closestCenter,
} from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { Search, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type {
  AgentProfileToolAssignment,
  SearchToolConfigResponse,
  SearchAssignableToolSlot,
} from "@/shared/api/types";

type SlotDefinition = {
  slot: SearchAssignableToolSlot;
  label: string;
  hint: string;
};

const SLOT_IDS: SlotDefinition[] = [
  {
    slot: "rag",
    label: "RAG",
    hint: "Document retrieval tool for grounded answers.",
  },
  {
    slot: "ontology_search",
    label: "Ontology Search",
    hint: "Ontology / graph search tool for entities and relations.",
  },
];

export function ToolSlotBoard({
  tools,
  assignments,
  onChange,
  visibleSlots,
}: {
  tools: SearchToolConfigResponse[];
  assignments: AgentProfileToolAssignment[];
  onChange: (assignments: AgentProfileToolAssignment[]) => void;
  /** When set, only these slots (graph vs vector backends) are configurable. */
  visibleSlots?: SearchAssignableToolSlot[];
}) {
  const [search, setSearch] = useState("");
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));

  const slotDefs = useMemo(() => {
    if (!visibleSlots?.length) return SLOT_IDS;
    const allow = new Set(visibleSlots);
    return SLOT_IDS.filter((s) => allow.has(s.slot));
  }, [visibleSlots]);

  const filteredTools = useMemo(() => {
    let list = tools;
    if (visibleSlots?.length) {
      const allow = new Set(visibleSlots);
      list = tools.filter((tool) => tool.assignable_slots.some((s) => allow.has(s)));
    }
    const query = search.trim().toLowerCase();
    return list.filter((tool) => {
      if (!query) return true;
      return `${tool.name} ${tool.description} ${tool.tool_name} ${tool.embedding_model}`
        .toLowerCase()
        .includes(query);
    });
  }, [search, tools, visibleSlots]);

  const assignmentBySlot = useMemo(() => {
    const mapping = new Map<SearchAssignableToolSlot, AgentProfileToolAssignment>();
    for (const assignment of assignments) {
      if (assignment.slot === "rag" || assignment.slot === "ontology_search") {
        mapping.set(assignment.slot, assignment);
      }
    }
    return mapping;
  }, [assignments]);

  const toolById = useMemo(() => new Map(tools.map((tool) => [tool.id, tool])), [tools]);

  function assignTool(slot: SearchAssignableToolSlot, tool: SearchToolConfigResponse) {
    const next = assignments.filter((item) => item.slot !== slot);
    next.push({
      slot,
      tool_name: tool.tool_name,
      config_id: tool.id,
      enabled: true,
      position: slot === "rag" ? 0 : 1,
    });
    onChange(
      next.sort((left, right) => {
        const leftPos = left.position ?? 0;
        const rightPos = right.position ?? 0;
        return leftPos - rightPos;
      }),
    );
  }

  function clearSlot(slot: SearchAssignableToolSlot) {
    onChange(assignments.filter((item) => item.slot !== slot));
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(event) => handleDragEnd(event, toolById, assignTool)}>
      <div className="space-y-4">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="grid gap-4 md:grid-cols-2">
            {slotDefs.map((slot) => {
              const assignment = assignmentBySlot.get(slot.slot) ?? null;
              const tool = assignment?.config_id ? toolById.get(assignment.config_id) ?? null : null;
              return (
                <SlotCard
                  key={slot.slot}
                  slot={slot}
                  tool={tool}
                  onClear={() => clearSlot(slot.slot)}
                />
              );
            })}
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search saved tool instances"
              />
            </div>
            <div className="space-y-3">
              {filteredTools.map((tool) => (
                <PaletteItem
                  key={tool.id}
                  tool={tool}
                  onAssign={(slot) => assignTool(slot, tool)}
                />
              ))}
              {filteredTools.length === 0 ? (
                <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
                  No assignable search tools match this filter.
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </DndContext>
  );
}

function handleDragEnd(
  event: DragEndEvent,
  toolById: Map<string, SearchToolConfigResponse>,
  assignTool: (slot: SearchAssignableToolSlot, tool: SearchToolConfigResponse) => void,
) {
  const { active, over } = event;
  if (!over) return;
  const tool = toolById.get(String(active.id));
  const slot = String(over.id) as SearchAssignableToolSlot;
  if (!tool || !tool.assignable_slots.includes(slot)) return;
  assignTool(slot, tool);
}

function SlotCard({
  slot,
  tool,
  onClear,
}: {
  slot: SlotDefinition;
  tool: SearchToolConfigResponse | null;
  onClear: () => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: slot.slot });
  return (
    <div
      ref={setNodeRef}
      className={`rounded-3xl border p-5 shadow-sm transition ${
        isOver ? "border-primary bg-primary/5" : "bg-background"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{slot.label}</div>
          <p className="mt-1 text-xs text-muted-foreground">{slot.hint}</p>
        </div>
        {tool ? (
          <Button type="button" variant="ghost" size="icon" onClick={onClear} aria-label={`Clear ${slot.label}`}>
            <X className="h-4 w-4" />
          </Button>
        ) : null}
      </div>

      {tool ? (
        <div className="mt-4 rounded-2xl border bg-muted/20 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <div className="font-medium">{tool.name}</div>
            {tool.is_system ? <Badge variant="secondary">system</Badge> : null}
            <Badge variant={tool.ready ? "success" : "warning"}>{tool.ready ? "ready" : "blocked"}</Badge>
          </div>
          <div className="mt-2 text-xs text-muted-foreground">{tool.description || tool.tool_name}</div>
          <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
            <span className="rounded bg-background px-2 py-1 font-mono">{tool.tool_name}</span>
            <span className="rounded bg-background px-2 py-1 font-mono">
              {tool.embedding_provider}::{tool.embedding_model}
            </span>
          </div>
        </div>
      ) : (
        <div className="mt-4 rounded-2xl border border-dashed p-6 text-sm text-muted-foreground">
          Drag a compatible saved tool instance here.
        </div>
      )}
    </div>
  );
}

function PaletteItem({
  tool,
  onAssign,
}: {
  tool: SearchToolConfigResponse;
  onAssign: (slot: SearchAssignableToolSlot) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id: tool.id });
  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.6 : 1,
  };
  return (
    <div ref={setNodeRef} style={style} className="rounded-2xl border bg-muted/10 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="font-medium">{tool.name}</div>
        {tool.is_system ? <Badge variant="secondary">default</Badge> : null}
        <Badge variant="outline" className="font-mono text-[10px]">
          {tool.tool_name}
        </Badge>
      </div>
      <div className="mt-1 text-xs text-muted-foreground">
        {tool.description || "Saved tool instance"}
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {tool.assignable_slots.map((slot) => (
          <Button key={slot} type="button" size="sm" variant="outline" onClick={() => onAssign(slot)}>
            Assign to {slot === "rag" ? "RAG" : "Ontology"}
          </Button>
        ))}
        <Button type="button" size="sm" {...listeners} {...attributes}>
          Drag
        </Button>
      </div>
    </div>
  );
}
