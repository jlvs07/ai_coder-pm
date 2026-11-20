"use client";

import { useState, type FormEvent } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card } from "@/lib/kanban";
import { EditIcon, TrashIcon } from "@/components/Icons";

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => Promise<void>;
  onUpdate: (
    cardId: string,
    title: string,
    details: string
  ) => Promise<boolean>;
};

export const KanbanCard = ({ card, onDelete, onUpdate }: KanbanCardProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(card.title);
  const [details, setDetails] = useState(card.details);
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: card.id, disabled: isEditing });

  const handleUpdate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const saved = await onUpdate(card.id, title.trim(), details.trim());
    if (saved) {
      setIsEditing(false);
    }
  };

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={clsx(
        "rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_12px_24px_rgba(3,33,71,0.08)]",
        "transition-all duration-150",
        isDragging && "opacity-60 shadow-[0_18px_32px_rgba(3,33,71,0.16)]"
      )}
      {...attributes}
      {...listeners}
      role="group"
      aria-label={card.title}
      aria-disabled={undefined}
      data-testid={`card-${card.id}`}
    >
      {isEditing ? (
        <form className="space-y-3" onSubmit={handleUpdate}>
          <input
            aria-label="Título de la tarjeta"
            className="w-full rounded-lg border border-[var(--stroke)] px-3 py-2 text-sm"
            onChange={(event) => setTitle(event.target.value)}
            required
            value={title}
          />
          <textarea
            aria-label="Detalles de la tarjeta"
            className="w-full rounded-lg border border-[var(--stroke)] px-3 py-2 text-sm"
            onChange={(event) => setDetails(event.target.value)}
            rows={3}
            value={details}
          />
          <div className="flex items-center gap-2">
            <button
              type="submit"
              className="rounded-full bg-[var(--secondary-purple)] px-3 py-2 text-xs font-semibold text-white"
            >
              Guardar cambios
            </button>
            <button
              type="button"
              onClick={() => {
                setTitle(card.title);
                setDetails(card.details);
                setIsEditing(false);
              }}
              className="rounded-full border border-[var(--stroke)] px-3 py-2 text-xs font-semibold text-[var(--gray-text)]"
            >
              Cancelar
            </button>
          </div>
        </form>
      ) : (
        <div className="flex items-start gap-2">
          <div className="min-w-0 flex-1">
            <h4 className="break-words font-display text-base font-semibold text-[var(--navy-dark)]">
              {card.title}
            </h4>
            <p className="mt-1.5 break-words text-sm leading-6 text-[var(--gray-text)]">
              {card.details}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-0.5">
            <button
              type="button"
              onClick={() => {
                setTitle(card.title);
                setDetails(card.details);
                setIsEditing(true);
              }}
              className="rounded-lg border border-transparent p-2 text-[var(--primary-blue)] transition hover:border-[var(--stroke)] hover:bg-[var(--surface)]"
              aria-label={`Editar ${card.title}`}
              title="Editar tarjeta"
            >
              <EditIcon />
            </button>
            <button
              type="button"
              onClick={() => void onDelete(card.id)}
              className="rounded-lg border border-transparent p-2 text-[var(--gray-text)] transition hover:border-[var(--stroke)] hover:bg-red-50 hover:text-red-600"
              aria-label={`Eliminar ${card.title}`}
              title="Eliminar tarjeta"
            >
              <TrashIcon />
            </button>
          </div>
        </div>
      )}
    </article>
  );
};
