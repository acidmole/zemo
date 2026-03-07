import type { GameState, Card } from "../../api/types";

interface Props {
  result: Record<string, unknown>;
  gameState: GameState;
  onClose: () => void;
}

export function CardInspect({ result, gameState, onClose }: Props) {
  const pickedCards = result.picked_cards as Card[] | undefined;
  const trapsTriggered = result.traps_triggered as Card[] | undefined;
  const trapDamage = result.trap_damage as number | undefined;
  const message = result.message as string | undefined;
  const revealedCards = result.revealed_cards as Card[] | undefined;

  const cards = pickedCards || revealedCards || [];

  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-title">
          Card Pickup
        </div>
        <div className="dialog-body">
          {/* Traps */}
          {trapsTriggered && trapsTriggered.length > 0 && (
            <div style={{
              background: "rgba(255, 51, 85, 0.1)",
              border: "1px solid #ff3355",
              borderRadius: 6,
              padding: 8,
              marginBottom: 12,
            }}>
              <div style={{ color: "#ff3355", fontWeight: 700, fontSize: "0.9rem", marginBottom: 4 }}>
                TRAP TRIGGERED!
              </div>
              {trapsTriggered.map((trap: Card) => (
                <div key={trap.id} style={{ fontSize: "0.8rem", color: "#e0e0e0" }}>
                  <strong>{trap.name}</strong>: {trap.description}
                </div>
              ))}
              {trapDamage !== undefined && trapDamage > 0 && (
                <div style={{ color: "#ff3355", fontSize: "0.85rem", marginTop: 4 }}>
                  You took {trapDamage} damage!
                </div>
              )}
            </div>
          )}

          {/* Items picked up */}
          {cards.length > 0 && (
            <div>
              <div style={{ fontSize: "0.8rem", color: "#00aaff", fontWeight: 700, marginBottom: 6 }}>
                Cards obtained:
              </div>
              {cards.map((card: Card) => (
                <div key={card.id} className="card-item">
                  <div className="card-name">{card.name}</div>
                  <div className="card-desc">{card.description}</div>
                  <div className="card-weight">Weight: {card.weight}</div>
                </div>
              ))}
            </div>
          )}

          {cards.length === 0 && !trapsTriggered?.length && (
            <p style={{ color: "#606080", textAlign: "center" }}>
              {message || "No cards at this space."}
            </p>
          )}

          {message && cards.length > 0 && (
            <p style={{ color: "#9090b0", fontSize: "0.8rem", marginTop: 8 }}>{message}</p>
          )}

          {/* Current player weight after pickup */}
          {gameState && (() => {
            const currentCharId = gameState.turn_order[gameState.current_player_index];
            const player = gameState.players.find((p) => p.id === currentCharId);
            if (!player) return null;
            const totalWeight = player.hand.reduce((s, c) => s + c.weight, 0);
            const isOver = totalWeight > player.capacity;
            return (
              <div style={{
                marginTop: 8,
                fontSize: "0.8rem",
                color: isOver ? "#ff3355" : "#9090b0",
                textAlign: "center",
              }}>
                Carry weight: {totalWeight} / {player.capacity}
                {isOver && " -- OVER CAPACITY! Drop cards from Player Info panel."}
              </div>
            );
          })()}
        </div>
        <div className="dialog-actions">
          <button className="btn btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
