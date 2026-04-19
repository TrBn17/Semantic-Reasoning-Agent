"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { MessageSquare, Plus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listAgentProfiles } from "@/lib/api/agent-profiles";
import { createConversation } from "@/lib/api/conversations";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";

export default function ChatLandingPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const {
    workspaceId,
    preferredAgentProfileId,
    setPreferredAgentProfileId,
  } = useWorkspaceStore();
  const { data: profiles } = useQuery({
    queryKey: queryKeys.agents.profiles(workspaceId),
    queryFn: () => listAgentProfiles(workspaceId),
  });

  const mutation = useMutation({
    mutationFn: () =>
      createConversation({
        title: "New conversation",
        workspace_id: workspaceId ?? undefined,
        agent_profile_id: preferredAgentProfileId ?? undefined,
      }),
    onSuccess: (c) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.all });
      router.push(`/ask/${c.id}`);
    },
    onError: (err) => toast.error(`Failed to create: ${(err as Error).message}`),
  });

  return (
    <div className="flex h-full items-center justify-center">
      <div className="max-w-md space-y-4 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <MessageSquare className="h-6 w-6 text-muted-foreground" />
        </div>
        <h2 className="text-lg font-semibold">Start a new conversation</h2>
        <p className="text-sm text-muted-foreground">
          Pick an agent profile and create a chat. Model routing will come from
          that profile or the workspace default.
        </p>
        <Select
          value={preferredAgentProfileId ?? "__default__"}
          onValueChange={(value) =>
            setPreferredAgentProfileId(value === "__default__" ? null : value)
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Select profile" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__default__">Workspace default</SelectItem>
            {(profiles ?? []).map((profile) => (
              <SelectItem key={profile.id} value={profile.id}>
                {profile.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          size="lg"
        >
          <Plus className="h-4 w-4" />
          New conversation
        </Button>
      </div>
    </div>
  );
}
