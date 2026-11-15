"use client";

import { useState, type FormEvent } from "react";
import type { BoardData } from "@/lib/kanban";
import type { ChatMessage } from "@/lib/kanbanApi";

type AIChatPanelProps = {
  onSend: (
    message: string,
    history: ChatMessage[]
  ) => Promise<{ reply: string; board: BoardData | null }>;
};

export const AIChatPanel = ({ onSend }: AIChatPanelProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const message = draft.trim();
    if (!message || isSending) {
      return;
    }

    const history = messages.slice(-20);
    setMessages((current) => [...current, { role: "user", content: message }]);
    setDraft("");
    setError(null);
    setIsSending(true);

    try {
      const response = await onSend(message, history);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: response.reply },
      ]);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The AI assistant could not complete the request."
      );
    } finally {
      setIsSending(false);
    }
  };

  return (
    <aside
      aria-labelledby="ai-chat-title"
      className="flex min-h-[520px] flex-col overflow-hidden rounded-3xl border border-[var(--stroke)] bg-white/95 shadow-[var(--shadow)]"
    >
      <header className="border-b border-[var(--stroke)] bg-[var(--navy-dark)] px-5 py-5 text-white">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/65">
          Kanban Studio
        </p>
        <h2
          id="ai-chat-title"
          className="mt-1 font-display text-xl font-semibold"
        >
          AI assistant
        </h2>
        <p className="mt-2 text-sm leading-5 text-white/75">
          Ask questions or request changes to your board.
        </p>
      </header>

      <div
        aria-label="Conversation"
        aria-live="polite"
        className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4"
        role="log"
      >
        {messages.length === 0 ? (
          <p className="my-auto rounded-2xl bg-[var(--surface)] p-4 text-sm leading-6 text-[var(--gray-text)]">
            Your current board is included as context. For example, ask me to
            create a card, move a task, or rename a column.
          </p>
        ) : (
          messages.map((message, index) => (
            <div
              key={`${index}-${message.role}`}
              className={
                message.role === "user"
                  ? "ml-8 self-end rounded-2xl rounded-br-sm bg-[var(--secondary-purple)] px-4 py-3 text-sm leading-5 text-white"
                  : "mr-5 self-start rounded-2xl rounded-bl-sm bg-[var(--surface)] px-4 py-3 text-sm leading-5 text-[var(--navy-dark)]"
              }
            >
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.15em] opacity-70">
                {message.role === "user" ? "You" : "AI assistant"}
              </p>
              <p className="whitespace-pre-wrap">{message.content}</p>
            </div>
          ))
        )}
        {isSending && (
          <p className="text-sm text-[var(--gray-text)]" role="status">
            Assistant is thinking...
          </p>
        )}
      </div>

      <div className="border-t border-[var(--stroke)] p-4">
        {error && (
          <p
            className="mb-3 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700"
            role="alert"
          >
            {error}
          </p>
        )}
        <form className="space-y-3" onSubmit={handleSubmit}>
          <label
            className="sr-only"
            htmlFor="ai-chat-message"
          >
            Message the AI assistant
          </label>
          <textarea
            id="ai-chat-message"
            className="min-h-24 w-full resize-y rounded-2xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--navy-dark)] outline-none transition placeholder:text-[var(--gray-text)] focus:border-[var(--primary-blue)]"
            disabled={isSending}
            maxLength={4000}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask the assistant..."
            value={draft}
          />
          <button
            className="w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isSending || !draft.trim()}
            type="submit"
          >
            {isSending ? "Sending..." : "Send message"}
          </button>
        </form>
      </div>
    </aside>
  );
};
