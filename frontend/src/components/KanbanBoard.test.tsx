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
    const input = within(column).getByLabelText("Column title");

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
      within(column).getByRole("button", { name: /add a card/i })
    );
    await user.type(within(column).getByPlaceholderText("Card title"), "New card");
    await user.type(within(column).getByPlaceholderText("Details"), "Notes");
    await user.click(within(column).getByRole("button", { name: /add card/i }));

    expect(await within(column).findByText("New card")).toBeVisible();
    expect(kanbanApi.createCard).toHaveBeenCalledWith(
      "col-backlog",
      "New card",
      "Notes"
    );

    await user.click(
      within(column).getByRole("button", { name: "Delete New card" })
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
      screen.getByRole("button", { name: "Edit Align roadmap themes" })
    );
    await user.clear(screen.getByRole("textbox", { name: "Card title" }));
    await user.type(
      screen.getByRole("textbox", { name: "Card title" }),
      "Updated roadmap"
    );
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByText("Updated roadmap")).toBeVisible();
    expect(kanbanApi.updateCard).toHaveBeenCalledWith(
      "card-1",
      "Updated roadmap",
      "Draft quarterly themes with impact statements and metrics."
    );
  });
});
