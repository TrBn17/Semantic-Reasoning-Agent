"use client";

import { useMemo, useState } from "react";
import {
  DndContext,
  type DragEndEvent,
  DragOverlay,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  closestCenter,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { AgentCapabilityToolSchema } from "@/shared/api/types";

const LANE_PALETTE = "lane-palette";
const LANE_ALLOWED = "lane-allowed";
const LANE_BLOCKED = "lane-blocked";

export type ToolDndBoardProps = {
  paletteTools: AgentCapabilityToolSchema[];
  allowedToolNames: string[];
  blockedToolNames: string[];
  onAllowedChange: (names: string[]) => void;
  onBlockedChange: (names: string[]) => void;
  labels: {
    lanePalette: string;
    lanePaletteHint: string;
    laneAllowed: string;
    laneAllowedHint: string;
    laneBlocked: string;
    laneBlockedHint: string;
    searchToolsPlaceholder: string;
    riskFilter: string;
    riskAll: string;
    riskLow: string;
    riskMedium: string;
    riskHigh: string;
    removeFromLane: string;
    noCatalogTools: string;
  };
};

export function ToolDndBoard({
  paletteTools,
  allowedToolNames,
  blockedToolNames,
  onAllowedChange,
  onBlockedChange,
  labels,
}: ToolDndBoardProps) {
  const [search, setSearch] = useState("");
  const [risk, setRisk] = useState<"all" | "low" | "medium" | "high">("all");
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
  );

  const toolByName = useMemo(() => {
    const m = new Map<string, AgentCapabilityToolSchema>();
    for (const t of paletteTools) m.set(t.tool_name, t);
    for (const name of allowedToolNames) {
      const found = paletteTools.find((x) => x.tool_name === name);
      if (found) m.set(name, found);
    }
    for (const name of blockedToolNames) {
      const found = paletteTools.find((x) => x.tool_name === name);
      if (found) m.set(name, found);
    }
    return m;
  }, [paletteTools, allowedToolNames, blockedToolNames]);

  const filteredPalette = useMemo(() => {
    const q = search.trim().toLowerCase();
    return paletteTools.filter((tool) => {
      if (allowedToolNames.includes(tool.tool_name) || blockedToolNames.includes(tool.tool_name)) {
        return false;
      }
      if (risk !== "all" && tool.risk_level !== risk) return false;
      if (!q) return true;
      return `${tool.tool_name} ${tool.label} ${tool.family} ${tool.description}`.toLowerCase().includes(q);
    });
  }, [paletteTools, allowedToolNames, blockedToolNames, search, risk]);

  const activeTool = activeId ? toolByName.get(activeId) ?? null : null;

  const removeAllowed = (name: string) => {
    onAllowedChange(allowedToolNames.filter((n) => n !== name));
  };
  const removeBlocked = (name: string) => {
    onBlockedChange(blockedToolNames.filter((n) => n !== name));
  };

  const onDragEnd = (event: DragEndEvent) => {
    setActiveId(null);
    const { active, over } = event;
    if (!over) return;

    const dragged = String(active.id);
    const overId = String(over.id);

    const dragFromAllowed = allowedToolNames.includes(dragged);
    const dragFromBlocked = blockedToolNames.includes(dragged);

    if (overId === LANE_BLOCKED || blockedToolNames.includes(overId)) {
      onAllowedChange(allowedToolNames.filter((n) => n !== dragged));
      const b = blockedToolNames.filter((n) => n !== dragged);
      if (!b.includes(dragged)) b.push(dragged);
      onBlockedChange(b);
      return;
    }

    if (overId === LANE_PALETTE) {
      onAllowedChange(allowedToolNames.filter((n) => n !== dragged));
      onBlockedChange(blockedToolNames.filter((n) => n !== dragged));
      return;
    }

    if (overId === LANE_ALLOWED) {
      onBlockedChange(blockedToolNames.filter((n) => n !== dragged));
      const without = allowedToolNames.filter((n) => n !== dragged);
      if (!without.includes(dragged)) onAllowedChange([...without, dragged]);
      else onAllowedChange(without);
      return;
    }

    if (allowedToolNames.includes(overId)) {
      onBlockedChange(blockedToolNames.filter((n) => n !== dragged));
      if (dragFromAllowed) {
        const oldI = allowedToolNames.indexOf(dragged);
        const newI = allowedToolNames.indexOf(overId);
        if (oldI >= 0 && newI >= 0 && oldI !== newI) {
          onAllowedChange(arrayMove(allowedToolNames, oldI, newI));
        }
        return;
      }
      const without = allowedToolNames.filter((n) => n !== dragged);
      const targetIndex = without.indexOf(overId);
      if (targetIndex >= 0) {
        without.splice(targetIndex, 0, dragged);
        onAllowedChange(without);
      } else {
        onAllowedChange([...without, dragged]);
      }
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={({ active }) => setActiveId(String(active.id))}
      onDragEnd={onDragEnd}
      onDragCancel={() => setActiveId(null)}
    >
      <div className="grid gap-4 lg:grid-cols-3">
        <PaletteLane id={LANE_PALETTE} title={labels.lanePalette} hint={labels.lanePaletteHint} tools={filteredPalette} />
        <AllowedLane
          id={LANE_ALLOWED}
          title={labels.laneAllowed}
          hint={labels.laneAllowedHint}
          allowedToolNames={allowedToolNames}
          toolByName={toolByName}
          onRemove={removeAllowed}
          removeLabel={labels.removeFromLane}
        />
        <BlockedLane
          id={LANE_BLOCKED}
          title={labels.laneBlocked}
          hint={labels.laneBlockedHint}
          blockedToolNames={blockedToolNames}
          toolByName={toolByName}
          onRemove={removeBlocked}
          removeLabel={labels.removeFromLane}
        />
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1 space-y-2">
          <Label className="text-xs">{labels.searchToolsPlaceholder}</Label>
          <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={labels.searchToolsPlaceholder} />
        </div>
        <div className="space-y-2 sm:w-44">
          <Label className="text-xs">{labels.riskFilter}</Label>
          <Select value={risk} onValueChange={(v) => setRisk(v as typeof risk)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{labels.riskAll}</SelectItem>
              <SelectItem value="low">{labels.riskLow}</SelectItem>
              <SelectItem value="medium">{labels.riskMedium}</SelectItem>
              <SelectItem value="high">{labels.riskHigh}</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {paletteTools.length === 0 && (
        <p className="mt-3 text-sm text-muted-foreground">{labels.noCatalogTools}</p>
      )}

      <DragOverlay>
        {activeTool ? (
          <div className="rounded-lg border bg-card px-3 py-2 text-sm shadow-lg">
            <div className="font-medium">{activeTool.label}</div>
            <div className="text-xs text-muted-foreground">{activeTool.tool_name}</div>
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}

function PaletteLane({
  id,
  title,
  hint,
  tools,
}: {
  id: string;
  title: string;
  hint: string;
  tools: AgentCapabilityToolSchema[];
}) {
  const { setNodeRef, isOver } = useDroppable({ id });
  return (
    <div
      ref={setNodeRef}
      className={`flex min-h-[220px] flex-col rounded-2xl border p-3 ${isOver ? "border-primary ring-1 ring-primary/30" : ""}`}
    >
      <div className="mb-1 font-semibold">{title}</div>
      <p className="mb-2 text-xs text-muted-foreground">{hint}</p>
      <ScrollArea className="max-h-[320px] pr-2">
        <div className="space-y-2">
          {tools.map((tool) => (
            <PaletteDraggable key={tool.tool_name} tool={tool} />
          ))}
          {tools.length === 0 && <p className="text-xs text-muted-foreground">—</p>}
        </div>
      </ScrollArea>
    </div>
  );
}

function PaletteDraggable({ tool }: { tool: AgentCapabilityToolSchema }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: tool.tool_name,
  });
  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`, opacity: isDragging ? 0.5 : 1 }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex cursor-grab items-start gap-2 rounded-xl border bg-card p-2 active:cursor-grabbing"
      {...listeners}
      {...attributes}
    >
      <GripVertical className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-1">
          <span className="text-sm font-medium">{tool.label}</span>
          <Badge variant="outline" className="text-[10px]">
            {tool.family}
          </Badge>
          <Badge variant="secondary" className="text-[10px]">
            {tool.risk_level}
          </Badge>
        </div>
        <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{tool.description}</p>
        <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">{tool.tool_name}</p>
      </div>
    </div>
  );
}

function AllowedLane({
  id,
  title,
  hint,
  allowedToolNames,
  toolByName,
  onRemove,
  removeLabel,
}: {
  id: string;
  title: string;
  hint: string;
  allowedToolNames: string[];
  toolByName: Map<string, AgentCapabilityToolSchema>;
  onRemove: (name: string) => void;
  removeLabel: string;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });
  return (
    <div
      ref={setNodeRef}
      className={`flex min-h-[220px] flex-col rounded-2xl border p-3 ${isOver ? "border-primary ring-1 ring-primary/30" : ""}`}
    >
      <div className="mb-1 font-semibold">{title}</div>
      <p className="mb-2 text-xs text-muted-foreground">{hint}</p>
      <SortableContext items={allowedToolNames} strategy={verticalListSortingStrategy}>
        <ScrollArea className="max-h-[320px] pr-2">
          <div className="space-y-2">
            {allowedToolNames.map((name) => (
              <SortableAllowedItem
                key={name}
                toolName={name}
                tool={toolByName.get(name)}
                onRemove={() => onRemove(name)}
                removeLabel={removeLabel}
              />
            ))}
            {allowedToolNames.length === 0 && <p className="text-xs text-muted-foreground">—</p>}
          </div>
        </ScrollArea>
      </SortableContext>
    </div>
  );
}

function SortableAllowedItem({
  toolName,
  tool,
  onRemove,
  removeLabel,
}: {
  toolName: string;
  tool?: AgentCapabilityToolSchema;
  onRemove: () => void;
  removeLabel: string;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: toolName });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.55 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className="flex items-start gap-2 rounded-xl border bg-card p-2">
      <button
        type="button"
        className="mt-0.5 cursor-grab text-muted-foreground active:cursor-grabbing"
        {...listeners}
        {...attributes}
      >
        <GripVertical className="h-4 w-4" />
      </button>
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium">{tool?.label ?? toolName}</div>
        <p className="font-mono text-[10px] text-muted-foreground">{toolName}</p>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-8 w-8 shrink-0"
        title={removeLabel}
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}

function BlockedLane({
  id,
  title,
  hint,
  blockedToolNames,
  toolByName,
  onRemove,
  removeLabel,
}: {
  id: string;
  title: string;
  hint: string;
  blockedToolNames: string[];
  toolByName: Map<string, AgentCapabilityToolSchema>;
  onRemove: (name: string) => void;
  removeLabel: string;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });
  return (
    <div
      ref={setNodeRef}
      className={`flex min-h-[220px] flex-col rounded-2xl border p-3 ${isOver ? "border-destructive/50 ring-1 ring-destructive/30" : ""}`}
    >
      <div className="mb-1 font-semibold">{title}</div>
      <p className="mb-2 text-xs text-muted-foreground">{hint}</p>
      <ScrollArea className="max-h-[320px] pr-2">
        <div className="space-y-2">
          {blockedToolNames.map((name) => (
            <BlockedDraggable
              key={name}
              toolName={name}
              tool={toolByName.get(name)}
              onRemove={() => onRemove(name)}
              removeLabel={removeLabel}
            />
          ))}
          {blockedToolNames.length === 0 && <p className="text-xs text-muted-foreground">—</p>}
        </div>
      </ScrollArea>
    </div>
  );
}

function BlockedDraggable({
  toolName,
  tool,
  onRemove,
  removeLabel,
}: {
  toolName: string;
  tool?: AgentCapabilityToolSchema;
  onRemove: () => void;
  removeLabel: string;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id: toolName });
  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`, opacity: isDragging ? 0.5 : 1 }
    : undefined;

  return (
    <div ref={setNodeRef} style={style} className="flex items-start gap-2 rounded-xl border bg-card p-2">
      <button
        type="button"
        className="mt-0.5 cursor-grab text-muted-foreground active:cursor-grabbing"
        {...listeners}
        {...attributes}
      >
        <GripVertical className="h-4 w-4" />
      </button>
      <div className="min-w-0 flex-1 cursor-grab" {...listeners} {...attributes}>
        <div className="text-sm font-medium">{tool?.label ?? toolName}</div>
        <p className="font-mono text-[10px] text-muted-foreground">{toolName}</p>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-8 w-8 shrink-0"
        title={removeLabel}
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}
