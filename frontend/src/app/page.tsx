import { KanbanBoard } from "@/components/KanbanBoard";
import { SessionGate } from "@/components/SessionGate";

export default function Home() {
  return (
    <SessionGate>
      <KanbanBoard />
    </SessionGate>
  );
}
