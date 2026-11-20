import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData } from "@/lib/kanban";
import * as kanbanApi from "@/lib/kanbanApi";

vi.mock("@/lib/kanbanApi", () => ({
  createCard: vi.fn(),
  deleteCard: vi.fn(),
  getBoard: vi.fn(),
  renameColumn: vi.fn(),
  saveCardOrder: vi.fn(),
  sendBoardChat: vi.fn(),
  updateCard: vi.fn(),
}));

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(kanbanApi.getBoard).mockResolvedValue(structuredClone(initialData));
    vi.mocked(kanbanApi.createCard).mockResolvedValue({
      id: "card-new",
      title: "New card",
      details: "Notes",
    });
    vi.mocked(kanbanApi.deleteCard).mockResolvedValue(undefined);
    vi.mocked(kanbanApi.renameColumn).mockImplementation(
      async (columnId, title) => ({ id: columnId, title })
    );
    vi.mocked(kanbanApi.updateCard).mockImplementation(
      async (cardId, title, details) => ({ id: cardId, title, details })
    );
    vi.mocked(kanbanApi.saveCardOrder).mockResolvedValue({ status: "ok" });
    vi.mocked(kanbanApi.sendBoardChat).mockResolvedValue({
      reply: "I can help with your board.",
      board: null,
    });
  });

  it("loads the board from the API and renders five columns", async () => {
    render(<KanbanBoard />);

    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
    expect(kanbanApi.getBoard).toHaveBeenCalledOnce();
    expect(screen.getByText("Align roadmap themes")).toBeVisible();
  });

  it("shows a clear error instead of demo data when board loading fails", async () => {
    vi.mocked(kanbanApi.getBoard).mockRejectedValue(
      new Error("API unavailable")
    );
    render(<KanbanBoard />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "API unavailable"
    );
    expect(screen.queryByTestId(/column-/i)).not.toBeInTheDocument();
  });

  it("renames a column through the API", async () => {
    const user = userEvent.setup();
    render(<KanbanBoard />);
    const column = await screen.findAllByTestId(/column-/i).then((items) => items[0]);
    const input = within(column).getByLabelText("Título de la columna");

    await user.clear(input);
    await user.type(input, "New Name");
    await user.tab();

    await waitFor(() => {
      expect(kanbanApi.renameColumn).toHaveBeenCalledWith(
        "col-backlog",
        "New Name"
      );
    });
    expect(input).toHaveValue("New Name");
  });

  it("creates and deletes a card through the API", async () => {
    const user = userEvent.setup();
    render(<KanbanBoard />);
    const column = await screen.findAllByTestId(/column-/i).then((items) => items[0]);

    await user.click(
      within(column).getByRole("button", { name: /añadir una tarjeta/i })
    );
    await user.type(within(column).getByPlaceholderText("Título de la tarjeta"), "New card");
    await user.type(within(column).getByPlaceholderText("Detalles"), "Notes");
    await user.click(within(column).getByRole("button", { name: "Crear tarjeta" }));

    expect(await within(column).findByText("New card")).toBeVisible();
    expect(kanbanApi.createCard).toHaveBeenCalledWith(
      "col-backlog",
      "New card",
      "Notes"
    );

    await user.click(
      within(column).getByRole("button", { name: "Eliminar New card" })
    );
    await waitFor(() => {
      expect(kanbanApi.deleteCard).toHaveBeenCalledWith("card-new");
    });
    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });

  it("edits a card through the API", async () => {
    const user = userEvent.setup();
    render(<KanbanBoard />);
    await screen.findByText("Align roadmap themes");
    await user.click(
      screen.getByRole("button", { name: "Editar Align roadmap themes" })
    );
    await user.clear(screen.getByRole("textbox", { name: "Título de la tarjeta" }));
    await user.type(
      screen.getByRole("textbox", { name: "Título de la tarjeta" }),
      "Updated roadmap"
    );
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }));

    expect(await screen.findByText("Updated roadmap")).toBeVisible();
    expect(kanbanApi.updateCard).toHaveBeenCalledWith(
      "card-1",
      "Updated roadmap",
      "Draft quarterly themes with impact statements and metrics."
    );
  });

  it("sends chat history and synchronizes AI board changes", async () => {
    const user = userEvent.setup();
    const updatedBoard = structuredClone(initialData);
    updatedBoard.cards["card-1"].title = "AI updated roadmap";
    vi.mocked(kanbanApi.sendBoardChat)
      .mockResolvedValueOnce({
        reply: "I will update that card.",
        board: updatedBoard,
      })
      .mockResolvedValueOnce({
        reply: "The update is complete.",
        board: null,
      });

    render(<KanbanBoard />);
    await screen.findByText("Align roadmap themes");
    const input = screen.getByRole("textbox", {
      name: "Escribe al asistente IA",
    });

    await user.type(input, "Rename the roadmap card");
    await user.click(screen.getByRole("button", { name: "Enviar mensaje" }));

    expect(await screen.findByText("AI updated roadmap")).toBeVisible();
    expect(await screen.findByText("I will update that card.")).toBeVisible();
    await user.click(
      screen.getByRole("button", { name: "Editar AI updated roadmap" })
    );
    expect(screen.getByRole("textbox", { name: "Título de la tarjeta" })).toHaveValue(
      "AI updated roadmap"
    );
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(kanbanApi.sendBoardChat).toHaveBeenNthCalledWith(
      1,
      "Rename the roadmap card",
      []
    );

    await user.type(input, "What changed?");
    await user.click(screen.getByRole("button", { name: "Enviar mensaje" }));

    expect(await screen.findByText("The update is complete.")).toBeVisible();
    expect(kanbanApi.sendBoardChat).toHaveBeenNthCalledWith(
      2,
      "What changed?",
      [
        { role: "user", content: "Rename the roadmap card" },
        { role: "assistant", content: "I will update that card." },
      ]
    );
  });

  it("shows chat errors without changing the displayed board", async () => {
    const user = userEvent.setup();
    vi.mocked(kanbanApi.sendBoardChat).mockRejectedValue(
      new Error("OpenRouter unavailable")
    );

    render(<KanbanBoard />);
    await screen.findByText("Align roadmap themes");
    await user.type(
      screen.getByRole("textbox", { name: "Escribe al asistente IA" }),
      "Move a card"
    );
    await user.click(screen.getByRole("button", { name: "Enviar mensaje" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "OpenRouter unavailable"
    );
    expect(screen.getByText("Align roadmap themes")).toBeVisible();
    expect(screen.queryByText("AI updated roadmap")).not.toBeInTheDocument();
  });
});
