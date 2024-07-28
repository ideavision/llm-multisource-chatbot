export async function createChatSession(passistId?: number | null) {
  const chatSessionResponse = await fetch("/api/chat/create-chat-session", {
    method: "POST",
    body: JSON.stringify({
      passist_id: passistId,
    }),
    headers: {
      "Content-Type": "application/json",
    },
  });
  return chatSessionResponse;
}
