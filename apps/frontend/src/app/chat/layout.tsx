import type { ReactNode } from "react";
import { ConversationList } from "@/components/chat/conversation-list";

export default function ChatLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-full">
      <ConversationList />
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
