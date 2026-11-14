import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { SessionGate } from "@/components/SessionGate";

describe("SessionGate", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    cleanup();
  });

  it("shows the login form when there is no saved session", async () => {
    render(
      <SessionGate>
        <p>Protected board</p>
      </SessionGate>
    );

    expect(await screen.findByRole("heading", { name: "Inicia sesión" })).toBeVisible();
    expect(screen.queryByText("Protected board")).not.toBeInTheDocument();
  });

  it("rejects incorrect credentials without exposing the board", async () => {
    const user = userEvent.setup();
    render(
      <SessionGate>
        <p>Protected board</p>
      </SessionGate>
    );

    await user.type(await screen.findByLabelText("Usuario"), "wrong");
    await user.type(screen.getByLabelText("Contraseña"), "wrong");
    await user.click(screen.getByRole("button", { name: "Acceder" }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Usuario o contraseña incorrectos."
    );
    expect(screen.queryByText("Protected board")).not.toBeInTheDocument();
    expect(localStorage.getItem("kanban-mvp-session")).toBeNull();
  });

  it("persists a valid session and returns to login after logout", async () => {
    const user = userEvent.setup();
    const board = (
      <SessionGate>
        <p>Protected board</p>
      </SessionGate>
    );
    const { rerender } = render(board);

    await user.type(await screen.findByLabelText("Usuario"), "usuario");
    await user.type(screen.getByLabelText("Contraseña"), "contraseña");
    await user.click(screen.getByRole("button", { name: "Acceder" }));

    expect(await screen.findByText("Protected board")).toBeVisible();
    expect(localStorage.getItem("kanban-mvp-session")).toBe("authenticated");

    rerender(board);
    await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));

    expect(await screen.findByRole("heading", { name: "Inicia sesión" })).toBeVisible();
    expect(screen.queryByText("Protected board")).not.toBeInTheDocument();
    expect(localStorage.getItem("kanban-mvp-session")).toBeNull();
  });
});
