import type { BoardData, Card } from "@/lib/kanban";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
const username = "usuario";

const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail =
      typeof body?.detail === "string" ? body.detail : response.statusText;
    throw new Error(`La solicitud falló (${response.status}): ${detail}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
};

export const getBoard = () =>
  request<BoardData>(`/api/boards/${encodeURIComponent(username)}`);

export const createCard = (columnId: string, title: string, details: string) =>
  request<Card>(
    `/api/boards/${encodeURIComponent(username)}/columns/${encodeURIComponent(columnId)}/cards`,
    {
      method: "POST",
      body: JSON.stringify({ title, details }),
    }
  );

export const updateCard = (
  cardId: string,
  title: string,
  details: string
) =>
  request<Card>(
    `/api/boards/${encodeURIComponent(username)}/cards/${encodeURIComponent(cardId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ title, details }),
    }
  );

export const deleteCard = (cardId: string) =>
  request<void>(
    `/api/boards/${encodeURIComponent(username)}/cards/${encodeURIComponent(cardId)}`,
    { method: "DELETE" }
  );

export const renameColumn = (columnId: string, title: string) =>
  request<{ id: string; title: string }>(
    `/api/boards/${encodeURIComponent(username)}/columns/${encodeURIComponent(columnId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }
  );

export const saveCardOrder = (board: BoardData) =>
  request<{ status: string }>(
    `/api/boards/${encodeURIComponent(username)}/cards/order`,
    {
      method: "PUT",
      body: JSON.stringify({
        columns: board.columns.map(({ id, cardIds }) => ({
          columnId: id,
          cardIds,
        })),
      }),
    }
  );

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type BoardChatResponse = {
  reply: string;
  board: BoardData | null;
};

export const sendBoardChat = (message: string, history: ChatMessage[]) =>
  request<BoardChatResponse>(`/api/boards/${encodeURIComponent(username)}/chat`, {
    method: "POST",
    body: JSON.stringify({ message, history }),
  });
