"use client";

import { useSearchParams } from "next/navigation";
import { ChatSession } from "./interfaces";
import { ChatSidebar } from "./sessionSidebar/ChatSidebar";
import { Chat } from "./Chat";
import { DocumentSet, Tag, User, ValidSources } from "@/lib/types";
import { Passist } from "../admin/passists/interfaces";
import { Header } from "@/components/Header";
import { HealthCheckBanner } from "@/components/health/healthcheck";
import { ApiKeyModal } from "@/components/openai/ApiKeyModal";
import { InstantSSRAutoRefresh } from "@/components/SSRAutoRefresh";

export function ChatLayout({
  user,
  chatSessions,
  availableSources,
  availableDocumentSets,
  availablePassists,
  availableTags,
  defaultSelectedPassistId,
  documentSidebarInitialWidth,
}: {
  user: User | null;
  chatSessions: ChatSession[];
  availableSources: ValidSources[];
  availableDocumentSets: DocumentSet[];
  availablePassists: Passist[];
  availableTags: Tag[];
  defaultSelectedPassistId?: number; // what passist to default to
  documentSidebarInitialWidth?: number;
}) {
  const searchParams = useSearchParams();
  const chatIdRaw = searchParams.get("chatId");
  const chatId = chatIdRaw ? parseInt(chatIdRaw) : null;

  const selectedChatSession = chatSessions.find(
    (chatSession) => chatSession.id === chatId
  );

  return (
    <>
      <div className="absolute top-0 z-40 w-full">
        <Header user={user} />
      </div>
      <HealthCheckBanner />
      <ApiKeyModal />
      <InstantSSRAutoRefresh />

      <div className="flex relative bg-background text-default overflow-x-hidden">
        <ChatSidebar
          existingChats={chatSessions}
          currentChatId={chatId}
          user={user}
        />

        <Chat
          existingChatSessionId={chatId}
          existingChatSessionPassistId={selectedChatSession?.passist_id}
          availableSources={availableSources}
          availableDocumentSets={availableDocumentSets}
          availablePassists={availablePassists}
          availableTags={availableTags}
          defaultSelectedPassistId={defaultSelectedPassistId}
          documentSidebarInitialWidth={documentSidebarInitialWidth}
        />
      </div>
    </>
  );
}
