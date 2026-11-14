describe("Kanban board", () => {
  beforeEach(() => {
    cy.clearLocalStorage();
  });

  const login = () => {
    cy.visit("/");
    cy.get('input[autocomplete="username"]').type("usuario");
    cy.get('input[autocomplete="current-password"]').type("contraseña");
    cy.contains("button", "Acceder").click();
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
  });

  it("adds a card to the first column", () => {
    login();

    cy.get('[data-testid^="column-"]').first().within(() => {
      cy.contains("button", "Add a card").click();
      cy.get('input[placeholder="Card title"]').type("Cypress card");
      cy.get('textarea[placeholder="Details"]').type("Added via Cypress");
      cy.contains("button", "Add card").click();
      cy.contains("Cypress card").should("be.visible");
    });
  });

  it("renames a column", () => {
    login();

    cy.get('[data-testid^="column-"]').first().within(() => {
      cy.get('input[aria-label="Column title"]').clear().type("Sprint board");
      cy.get('input[aria-label="Column title"]').should("have.value", "Sprint board");
    });
  });
});
