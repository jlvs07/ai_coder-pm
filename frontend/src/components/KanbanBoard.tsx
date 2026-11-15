"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  pointerWithin,
  useSensor,
  useSensors,
  closestCorners,
  type CollisionDetection,
  type DragMoveEvent,
  type DragOverEvent,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { AIChatPanel } from "@/components/AIChatPanel";
import { moveCard, type BoardData } from "@/lib/kanban";
import {
  createCard,
  deleteCard,
  getBoard,
  renameColumn,
  saveCardOrder,
  sendBoardChat,
  updateCard,
  type ChatMessage,
} from "@/lib/kanbanApi";

type DropTarget = {
  columnId: string;
  index: number;
  position: "before" | "after";
};

const resolveDropTarget = (
  columns: BoardData["columns"],
  activeId: string,
  overId: string,
  activeRect: { top: number; height: number } | null,
  overRect: { top: number; height: number }
): DropTarget | null => {
  if (activeId === overId) {
    return null;
  }

  const column = columns.find(
    (candidate) =>
      candidate.id === overId || candidate.cardIds.includes(overId)
  );
  if (!column) {
    return null;
  }

  const cardIds = column.cardIds.filter((cardId) => cardId !== activeId);
  if (column.id === overId) {
    return { columnId: column.id, index: cardIds.length, position: "after" };
  }

  const overIndex = cardIds.indexOf(overId);
  if (overIndex === -1) {
    return null;
  }

  const isAfter =
    activeRect !== null &&
    activeRect.top + activeRect.height / 2 >
      overRect.top + overRect.height / 2;

  return {
    columnId: column.id,
    index: overIndex + (isAfter ? 1 : 0),
    position: isAfter ? "after" : "before",
  };
};

export const KanbanBoard = () => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<DropTarget | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const overRef = useRef<DragOverEvent["over"]>(null);

  useEffect(() => {
    let isMounted = true;

    getBoard()
      .then((loadedBoard) => {
        if (isMounted) {
          setBoard(loadedBoard);
          setError(null);
        }
      })
      .catch((cause: unknown) => {
        if (isMounted) {
          setError(
            cause instanceof Error
              ? cause.message
              : "No se pudo cargar el tablero."
          );
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const runMutation = async (mutation: () => Promise<void>) => {
    if (isSaving) {
      return false;
    }

    setIsSaving(true);
    setError(null);
    try {
      await mutation();
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "No se pudo guardar el cambio."
      );
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const cardsById = useMemo(() => board?.cards ?? {}, [board?.cards]);

  const collisionDetection = useCallback<CollisionDetection>(
    (args) => {
      if (!args.pointerCoordinates) {
        return closestCorners(args);
      }

      const collisions = pointerWithin(args);
      if (!board) {
        return collisions;
      }
      if (collisions.some(({ id }) => id === args.active.id)) {
        return collisions.filter(({ id }) => id === args.active.id);
      }
      if (collisions.length === 0) {
        return [];
      }

      const cardCollisions = collisions.filter(({ id }) =>
        board.cards[String(id)]
      );
      if (cardCollisions.length > 0) {
        return cardCollisions;
      }

      const overColumn = collisions.find(({ id }) =>
        board.columns.some((column) => column.id === String(id))
      );
      if (overColumn) {
        const column = board.columns.find(
          (candidate) => candidate.id === String(overColumn.id)
        );
        const cardIds = new Set(
          column?.cardIds.filter((cardId) => cardId !== String(args.active.id)) ??
            []
        );
        const nearestCards = closestCorners(args).filter(({ id }) =>
          cardIds.has(String(id))
        );
        if (nearestCards.length > 0) {
          return [nearestCards[0]];
        }
      }

      return collisions;
    },
    [board]
  );

  const updateDropTarget = (
    activeId: string,
    over: DragOverEvent["over"]
  ) => {
    if (!board || !over) {
      setDropTarget(null);
      return;
    }

    setDropTarget(
      resolveDropTarget(
        board.columns,
        activeId,
        String(over.id),
        null,
        over.rect
      )
    );
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
    setDropTarget(null);
    overRef.current = null;
  };

  const handleDragOver = (event: DragOverEvent) => {
    overRef.current = event.over;
    updateDropTarget(String(event.active.id), event.over);
  };

  const handleDragMove = (event: DragMoveEvent) => {
    const over = overRef.current;
    if (!board || !over) {
      return;
    }

    setDropTarget(
      resolveDropTarget(
        board.columns,
        String(event.active.id),
        String(over.id),
        event.active.rect.current.translated,
        over.rect
      )
    );
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);
    setDropTarget(null);
    overRef.current = null;

    if (!over || active.id === over.id || !board) {
      return;
    }

    const target = resolveDropTarget(
      board.columns,
      String(active.id),
      String(over.id),
      active.rect.current.translated,
      over.rect
    );
    if (!target) {
      return;
    }

    const nextColumns = moveCard(
      board.columns,
      String(active.id),
      String(over.id),
      target.position
    );
    if (nextColumns === board.columns) {
      return;
    }

    void runMutation(async () => {
      await saveCardOrder({ ...board, columns: nextColumns });
      setBoard((current) =>
        current ? { ...current, columns: nextColumns } : current
      );
    });
  };

  const handleRenameColumn = async (columnId: string, title: string) => {
    if (!board) {
      return false;
    }
    return runMutation(async () => {
      await renameColumn(columnId, title);
      setBoard((current) =>
        current
          ? {
              ...current,
              columns: current.columns.map((column) =>
                column.id === columnId ? { ...column, title } : column
              ),
            }
          : current
      );
    });
  };

  const handleAddCard = async (
    columnId: string,
    title: string,
    details: string
  ) => {
    if (!board) {
      return false;
    }
    return runMutation(async () => {
      const card = await createCard(columnId, title, details || "No details yet.");
      setBoard((current) =>
        current
          ? {
              ...current,
              cards: { ...current.cards, [card.id]: card },
              columns: current.columns.map((column) =>
                column.id === columnId
                  ? { ...column, cardIds: [...column.cardIds, card.id] }
                  : column
              ),
            }
          : current
      );
    });
  };

  const handleUpdateCard = async (
    cardId: string,
    title: string,
    details: string
  ) => {
    if (!board) {
      return false;
    }
    return runMutation(async () => {
      const card = await updateCard(cardId, title, details);
      setBoard((current) =>
        current
          ? { ...current, cards: { ...current.cards, [cardId]: card } }
          : current
      );
    });
  };

  const handleDeleteCard = async (columnId: string, cardId: string) => {
    if (!board) {
      return;
    }
    await runMutation(async () => {
      await deleteCard(cardId);
      setBoard((current) =>
        current
          ? {
              ...current,
              cards: Object.fromEntries(
                Object.entries(current.cards).filter(([id]) => id !== cardId)
              ),
              columns: current.columns.map((column) =>
                column.id === columnId
                  ? {
                      ...column,
                      cardIds: column.cardIds.filter((id) => id !== cardId),
                    }
                  : column
              ),
            }
          : current
      );
    });
  };

  const handleAIChat = async (message: string, history: ChatMessage[]) => {
    const response = await sendBoardChat(message, history);
    if (response.board) {
      setBoard(response.board);
    }
    return response;
  };

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center text-[var(--navy-dark)]">
        Cargando tablero...
      </main>
    );
  }

  if (!board) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
        <p role="alert" className="text-sm text-red-700">
          No se pudo cargar el tablero. {error}
        </p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold text-white"
        >
          Reintentar
        </button>
      </main>
    );
  }

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1900px] flex-col gap-10 px-6 pb-16 pt-12">
        {error && (
          <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        )}
        {isSaving && (
          <p role="status" className="text-sm text-[var(--gray-text)]">
            Guardando cambios...
          </p>
        )}
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <DndContext
          sensors={sensors}
          collisionDetection={collisionDetection}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragMove={handleDragMove}
          onDragEnd={handleDragEnd}
          onDragCancel={() => {
            setActiveCardId(null);
            setDropTarget(null);
            overRef.current = null;
          }}
        >
          <div className="grid items-stretch gap-6 2xl:grid-cols-[minmax(0,1fr)_320px]">
            <section className="min-w-0 overflow-x-auto pb-2">
              <div className="grid min-w-[280px] gap-6 sm:min-w-[520px] sm:grid-cols-2 lg:min-w-[1000px] lg:grid-cols-5 2xl:min-w-[1100px]">
                {board.columns.map((column) => (
                  <KanbanColumn
                    key={`${column.id}-${column.title}`}
                    column={column}
                    cards={column.cardIds.map((cardId) => board.cards[cardId])}
                    onRename={handleRenameColumn}
                    onAddCard={handleAddCard}
                    onDeleteCard={handleDeleteCard}
                    onUpdateCard={handleUpdateCard}
                    activeCardId={activeCardId}
                    dropIndicatorIndex={
                      dropTarget?.columnId === column.id
                        ? dropTarget.index
                        : null
                    }
                  />
                ))}
              </div>
            </section>
            <AIChatPanel onSend={handleAIChat} />
          </div>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>
    </div>
  );
};
