"use client";

import {
  useState,
  useSyncExternalStore,
  type FormEvent,
  type ReactNode,
} from "react";

const SESSION_KEY = "kanban-mvp-session";
const SESSION_EVENT = "kanban-session-change";

const subscribeToSession = (callback: () => void) => {
  window.addEventListener("storage", callback);
  window.addEventListener(SESSION_EVENT, callback);

  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(SESSION_EVENT, callback);
  };
};

const getSessionSnapshot = () =>
  localStorage.getItem(SESSION_KEY) === "authenticated";

type SessionGateProps = {
  children: ReactNode;
};

export const SessionGate = ({ children }: SessionGateProps) => {
  const isAuthenticated = useSyncExternalStore(
    subscribeToSession,
    getSessionSnapshot,
    () => false
  );
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [hasInvalidCredentials, setHasInvalidCredentials] = useState(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (username !== "usuario" || password !== "contraseña") {
      setHasInvalidCredentials(true);
      return;
    }

    localStorage.setItem(SESSION_KEY, "authenticated");
    window.dispatchEvent(new Event(SESSION_EVENT));
    setHasInvalidCredentials(false);
  };

  const handleLogout = () => {
    localStorage.removeItem(SESSION_KEY);
    window.dispatchEvent(new Event(SESSION_EVENT));
  };

  if (isAuthenticated) {
    return (
      <>
        <div className="relative mx-auto flex max-w-[1500px] justify-end px-6 pt-6">
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-full border border-[var(--stroke)] bg-white px-4 py-2 text-sm font-semibold text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)]"
          >
            Cerrar sesión
          </button>
        </div>
        {children}
      </>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6 py-12">
      <section className="w-full max-w-md rounded-[32px] border border-[var(--stroke)] bg-white/90 p-8 shadow-[var(--shadow)]">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
          Kanban Studio
        </p>
        <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
          Inicia sesión
        </h1>
        <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
          Accede a tu tablero de proyecto.
        </p>
        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <label className="block text-sm font-semibold text-[var(--navy-dark)]">
            Usuario
            <input
              autoComplete="username"
              className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-4 py-3 font-normal outline-none transition focus:border-[var(--primary-blue)]"
              onChange={(event) => {
                setUsername(event.target.value);
                setHasInvalidCredentials(false);
              }}
              required
              value={username}
            />
          </label>
          <label className="block text-sm font-semibold text-[var(--navy-dark)]">
            Contraseña
            <input
              autoComplete="current-password"
              className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-4 py-3 font-normal outline-none transition focus:border-[var(--primary-blue)]"
              onChange={(event) => {
                setPassword(event.target.value);
                setHasInvalidCredentials(false);
              }}
              required
              type="password"
              value={password}
            />
          </label>
          {hasInvalidCredentials && (
            <p role="alert" className="text-sm font-medium text-red-700">
              Usuario o contraseña incorrectos.
            </p>
          )}
          <button
            className="w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold text-white transition hover:brightness-110"
            type="submit"
          >
            Acceder
          </button>
        </form>
      </section>
    </main>
  );
};
