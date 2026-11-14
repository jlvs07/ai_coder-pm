"use client";

import { useState } from "react";
import clsx from "clsx";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Card, Column } from "@/lib/kanban";
import { KanbanCard } from "@/components/KanbanCard";
import { NewCardForm } from "@/components/NewCardForm";

type KanbanColumnProps = {
  column: Column;
  cards: Card[];
  onRename: (columnId: string, title: string) => Promise<boolean>;
  onAddCard: (
    columnId: string,
    title: string,
    details: string
  ) => Promise<boolean>;
  onDeleteCard: (columnId: string, cardId: string) => Promise<void>;
  onUpdateCard: (
    cardId: string,
    title: string,
    details: string
  ) => Promise<boolean>;
  activeCardId: string | null;
  dropIndicatorIndex: number | null;
};

export const KanbanColumn = ({
  column,
  cards,
  onRename,
  onAddCard,
  onDeleteCard,
  onUpdateCard,
  activeCardId,
  dropIndicatorIndex,
}: KanbanColumnProps) => {
  const { setNodeRef, isOver } = useDroppable({ id: column.id });
  const [titleDraft, setTitleDraft] = useState(column.title);
  const activeCardIndex = activeCardId
    ? column.cardIds.indexOf(activeCardId)
    : -1;
  const indicatorSlot =
    dropIndicatorIndex === null
      ? null
      : dropIndicatorIndex +
        (activeCardIndex >= 0 && activeCardIndex < dropIndicatorIndex ? 1 : 0);

  const dropIndicator = (
    <div
      aria-hidden="true"
      className="h-1 rounded-full bg-[var(--primary-blue)] shadow-[0_0_10px_rgba(32,157,215,0.8)]"
      data-testid="drop-indicator"
    />
  );

  return (
    <section
      ref={setNodeRef}
      className={clsx(
        "flex min-h-[520px] flex-col rounded-3xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-4 shadow-[var(--shadow)] transition",
        isOver && "ring-2 ring-[var(--accent-yellow)]"
      )}
      data-testid={`column-${column.id}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="w-full">
          <div className="flex items-center gap-3">
            <div className="h-2 w-10 rounded-full bg-[var(--accent-yellow)]" />
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              {cards.length} cards
            </span>
          </div>
          <input
            value={titleDraft}
            onChange={(event) => setTitleDraft(event.target.value)}
            onBlur={async () => {
              const nextTitle = titleDraft.trim();
              if (!nextTitle || nextTitle === column.title) {
                setTitleDraft(column.title);
                return;
              }
              if (!(await onRename(column.id, nextTitle))) {
                setTitleDraft(column.title);
              }
            }}
            className="mt-3 w-full bg-transparent font-display text-lg font-semibold text-[var(--navy-dark)] outline-none"
            aria-label="Column title"
          />
        </div>
      </div>
      <div className="mt-4 flex flex-1 flex-col gap-3">
        <SortableContext items={column.cardIds} strategy={verticalListSortingStrategy}>
          {cards.length === 0 ? (
            <div className="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-[var(--stroke)] px-3 py-6 text-center text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              <div className="w-full space-y-3">
                {indicatorSlot === 0 && dropIndicator}
                <span>Drop a card here</span>
              </div>
            </div>
          ) : (
            <>
              {cards.map((card, index) => (
                <div className="contents" key={card.id}>
                  {indicatorSlot === index && dropIndicator}
                  <KanbanCard
                    card={card}
                    onDelete={(cardId) => onDeleteCard(column.id, cardId)}
                    onUpdate={onUpdateCard}
                  />
                </div>
              ))}
              {indicatorSlot === cards.length && dropIndicator}
            </>
          )}
        </SortableContext>
      </div>
      <NewCardForm
        onAdd={(title, details) => onAddCard(column.id, title, details)}
      />
    </section>
  );
};
