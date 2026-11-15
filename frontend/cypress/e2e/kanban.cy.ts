describe("Kanban board", () => {
  const starterCardIds = [
    "card-1",
    "card-2",
    "card-3",
    "card-4",
    "card-5",
    "card-6",
    "card-7",
    "card-8",
  ];
  const starterColumns = [
    { columnId: "col-backlog", cardIds: ["card-1", "card-2"] },
    { columnId: "col-discovery", cardIds: ["card-3"] },
    { columnId: "col-progress", cardIds: ["card-4", "card-5"] },
    { columnId: "col-review", cardIds: ["card-6"] },
    { columnId: "col-done", cardIds: ["card-7", "card-8"] },
  ];
  const starterCards = {
    "card-1": {
      title: "Align roadmap themes",
      details: "Draft quarterly themes with impact statements and metrics.",
    },
    "card-2": {
      title: "Gather customer signals",
      details: "Review support tags, sales notes, and churn feedback.",
    },
    "card-3": {
      title: "Prototype analytics view",
      details: "Sketch initial dashboard layout and key drill-downs.",
    },
    "card-4": {
      title: "Refine status language",
      details: "Standardize column labels and tone across the board.",
    },
    "card-5": {
      title: "Design card layout",
      details: "Add hierarchy and spacing for scanning dense lists.",
    },
    "card-6": {
      title: "QA micro-interactions",
      details: "Verify hover, focus, and loading states.",
    },
    "card-7": {
      title: "Ship marketing page",
      details: "Final copy approved and asset pack delivered.",
    },
    "card-8": {
      title: "Close onboarding sprint",
      details: "Document release notes and share internally.",
    },
  };

  const resetBoard = () => {
    cy.request("/api/boards/usuario").then(
      ({
        body,
      }: {
        body: {
          cards: Record<string, unknown>;
          columns: { id: string; title: string }[];
        };
      }) => {
        Object.keys(body.cards)
          .filter((cardId) => !starterCardIds.includes(cardId))
          .forEach((cardId) => {
            cy.request("DELETE", `/api/boards/usuario/cards/${cardId}`);
          });
        const starterColumnTitles: Record<string, string> = {
          "col-backlog": "Backlog",
          "col-discovery": "Discovery",
          "col-progress": "In Progress",
          "col-review": "Review",
          "col-done": "Done",
        };
        body.columns.forEach((column) => {
          const title = starterColumnTitles[column.id];
          if (title && column.title !== title) {
            cy.request("PATCH", `/api/boards/usuario/columns/${column.id}`, {
              title,
            });
          }
        });
        Object.entries(starterCards).forEach(([cardId, card]) => {
          cy.request("PATCH", `/api/boards/usuario/cards/${cardId}`, card);
        });
        cy.request("PUT", "/api/boards/usuario/cards/order", {
          columns: starterColumns,
        });
      }
    );
  };

  beforeEach(() => {
    cy.viewport(1440, 1200);
    cy.clearLocalStorage();
    resetBoard();
  });

  afterEach(() => {
    resetBoard();
  });

  const login = () => {
    cy.intercept("GET", "/api/boards/usuario").as("loadBoard");
    cy.visit("/");
    cy.get('input[autocomplete="username"]').type("usuario");
    cy.get('input[autocomplete="current-password"]').type("contraseña");
    cy.contains("button", "Acceder").click();
    cy.wait("@loadBoard");
  };

  it("requires login and reports invalid credentials", () => {
    cy.visit("/");

    cy.contains("h1", "Inicia sesión").should("be.visible");
    cy.get('[data-testid^="column-"]').should("not.exist");
    cy.get('input[autocomplete="username"]').type("incorrecto");
    cy.get('input[autocomplete="current-password"]').type("incorrecta");
    cy.contains("button", "Acceder").click();
    cy.contains('[role="alert"]', "Usuario o contraseña incorrectos.").should(
      "be.visible"
    );
    cy.get('[data-testid^="column-"]').should("not.exist");
  });

  it("logs in, preserves the session after reload, and logs out", () => {
    login();

    cy.contains("h1", "Kanban Studio").should("be.visible");
    cy.reload();
    cy.contains("h1", "Kanban Studio").should("be.visible");
    cy.contains("button", "Cerrar sesión").click();
    cy.contains("h1", "Inicia sesión").should("be.visible");
    cy.get('[data-testid^="column-"]').should("not.exist");
  });

  it("loads the Kanban board and shows the expected columns", () => {
    login();

    cy.contains("h1", "Kanban Studio").should("be.visible");
    cy.get('[data-testid^="column-"]').should("have.length", 5);
    cy.get('[data-testid="card-card-1"]').should("contain", "Align roadmap themes");
  });

  it("creates and deletes a card through the API and keeps it across reload", () => {
    login();
    cy.intercept("POST", "/api/boards/usuario/columns/col-backlog/cards").as(
      "createCard"
    );

    cy.get('[data-testid^="column-"]').first().within(() => {
      cy.contains("button", "Add a card").click();
      cy.get('input[placeholder="Card title"]').type("Cypress persisted card");
      cy.get('textarea[placeholder="Details"]').type("Added via Cypress");
      cy.contains("button", "Add card").click();
    });
    cy.wait("@createCard").its("response.statusCode").should("eq", 201);
    cy.contains("Cypress persisted card").should("be.visible");
    cy.reload();
    cy.contains("Cypress persisted card").should("be.visible");
    cy.get('[data-testid^="column-"]')
      .first()
      .find('[aria-label="Delete Cypress persisted card"]')
      .click();
    cy.contains("Cypress persisted card").should("not.exist");
  });

  it("renames a column and persists it after reload", () => {
    login();
    cy.intercept("PATCH", "/api/boards/usuario/columns/col-backlog").as(
      "renameColumn"
    );

    cy.get('[data-testid^="column-"]').first().within(() => {
      cy.get('input[aria-label="Column title"]')
        .clear()
        .type("Sprint board")
        .blur();
    });
    cy.wait("@renameColumn").its("response.statusCode").should("eq", 200);
    cy.reload();
    cy.get('[data-testid="column-col-backlog"] input').should(
      "have.value",
      "Sprint board"
    );
    cy.get('[data-testid="column-col-backlog"] input')
      .clear()
      .type("Backlog")
      .blur();
  });

  it("edits a card and persists the update after reload", () => {
    login();
    cy.intercept("PATCH", "/api/boards/usuario/cards/card-1").as("updateCard");

    cy.get('[data-testid="card-card-1"]')
      .find('[aria-label="Edit Align roadmap themes"]')
      .click();
    cy.get('[data-testid="card-card-1"]')
      .find('input[aria-label="Card title"]')
      .clear()
      .type("Updated roadmap");
    cy.get('[data-testid="card-card-1"]')
      .contains("button", "Save changes")
      .click();
    cy.wait("@updateCard").its("response.statusCode").should("eq", 200);
    cy.contains("Updated roadmap").should("be.visible");
    cy.reload();
    cy.contains("Updated roadmap").should("be.visible");
  });

  it("sends a chat request and applies the returned board update", () => {
    cy.request("/api/boards/usuario").then(({ body }) => {
      const updatedBoard = structuredClone(body);
      updatedBoard.cards["card-ai-e2e"] = {
        id: "card-ai-e2e",
        title: "AI-created task",
        details: "Added by the assistant",
      };
      updatedBoard.columns[0].cardIds.push("card-ai-e2e");
      cy.intercept("POST", "/api/boards/usuario/chat", {
        statusCode: 200,
        body: {
          reply: "I added the task to Backlog.",
          board: updatedBoard,
        },
      }).as("aiChat");
    });

    login();
    cy.get("#ai-chat-message").type("Create a task in Backlog");
    cy.contains("button", "Send message").click();

    cy.wait("@aiChat").then(({ request }) => {
      expect(request.body).to.deep.equal({
        message: "Create a task in Backlog",
        history: [],
      });
    });
    cy.contains("AI-created task").should("be.visible");
    cy.contains("I added the task to Backlog.").should("be.visible");
  });

  it("moves a card with pointer drag and persists its new column and order", () => {
    login();
    cy.intercept("PUT", "/api/boards/usuario/cards/order").as("saveOrder");

    cy.get('[data-testid="card-card-2"]').then(($card) => {
      const cardRect = $card[0].getBoundingClientRect();
      const startX = Math.round(cardRect.left + 20);
      const startY = Math.round(cardRect.top + 20);
      cy.get('[data-testid="card-card-4"]').then(($target) => {
        const targetRect = $target[0].getBoundingClientRect();
        const endX = Math.round(targetRect.left + targetRect.width / 2);
        const endY = Math.round(targetRect.top + targetRect.height / 2);

        cy.wrap($card)
          .trigger("pointerdown", {
            force: true,
            isPrimary: true,
            button: 0,
            clientX: startX,
            clientY: startY,
          })
          .wait(50)
          .trigger("pointermove", {
            force: true,
            isPrimary: true,
            button: 0,
            buttons: 1,
            clientX: startX + 10,
            clientY: startY + 10,
          })
          .wait(50)
          .trigger("pointermove", {
            force: true,
            isPrimary: true,
            button: 0,
            buttons: 1,
            clientX: endX,
            clientY: endY,
          })
          .wait(50)
          .trigger("pointerup", {
            force: true,
            isPrimary: true,
            button: 0,
            clientX: endX,
            clientY: endY,
          });
      });
    });
    cy.wait("@saveOrder").its("response.statusCode").should("eq", 200);
    cy.reload();
    cy.get('[data-testid="column-col-progress"] [data-testid="card-card-2"]')
      .should("be.visible");
  });

  it("moves a card with the keyboard and persists its new column and order", () => {
    login();

    cy.intercept("PUT", "/api/boards/usuario/cards/order").as("saveOrder");
    cy.get('[data-testid="card-card-1"]')
      .focus()
      .type(" ", { parseSpecialCharSequences: false })
      .type("{rightArrow}")
      .type(" ", { parseSpecialCharSequences: false });
    cy.wait("@saveOrder").its("response.statusCode").should("eq", 200);
    cy.reload();
    cy.get('[data-testid="column-col-discovery"] [data-testid="card-card-1"]')
      .should("be.visible");
  });
});
