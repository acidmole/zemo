import type { GameState } from "../../api/types";

interface Props {
  result: Record<string, unknown>;
  gameState: GameState;
  onClose: () => void;
  onContinue: (continueF: boolean) => void;
}

export function FightDialog({ result, gameState, onClose, onContinue }: Props) {
  const attackerId = result.attacker_id as string | undefined;
  const defenderId = result.defender_id as string | undefined;
  const attackerRoll = result.attacker_roll as number | undefined;
  const defenderRoll = result.defender_roll as number | undefined;
  const attackerTotal = result.attacker_total as number | undefined;
  const defenderTotal = result.defender_total as number | undefined;
  const damage = result.damage as number | undefined;
  const winnerId = result.winner_id as string | undefined;
  const loserId = result.loser_id as string | undefined;
  const tie = result.tie as boolean | undefined;
  const canContinue = result.can_continue as boolean | undefined;
  const defenderDied = result.defender_died as boolean | undefined;
  const attackerDied = result.attacker_died as boolean | undefined;
  const message = result.message as string | undefined;

  // Shooting result fields
  const hit = result.hit as boolean | undefined;
  const ducked = result.ducked as boolean | undefined;
  const shootDamage = result.shoot_damage as number | undefined;

  const attacker = gameState.players.find((p) => p.id === attackerId);
  const defender = gameState.players.find((p) => p.id === defenderId);
  const winner = gameState.players.find((p) => p.id === winnerId);
  const loser = gameState.players.find((p) => p.id === loserId);

  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-title">
          {hit !== undefined ? "Shooting Result" : "Fight Result"}
        </div>
        <div className="dialog-body">
          {/* Combatants */}
          {attacker && defender && (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 20, marginBottom: 16 }}>
              <div style={{ textAlign: "center" }}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: "50%",
                    backgroundColor: attacker.color,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 800,
                    fontSize: "1.2rem",
                    color: "#fff",
                    margin: "0 auto 4px",
                  }}
                >
                  {attacker.name.charAt(0)}
                </div>
                <div style={{ fontWeight: 600, fontSize: "0.85rem", color: attacker.color }}>{attacker.name}</div>
                {attackerRoll !== undefined && (
                  <div style={{ fontSize: "0.8rem", fontFamily: "monospace" }}>
                    Roll: {attackerRoll} {attackerTotal !== undefined && `(Total: ${attackerTotal})`}
                  </div>
                )}
              </div>
              <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#606080" }}>VS</div>
              <div style={{ textAlign: "center" }}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: "50%",
                    backgroundColor: defender.color,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 800,
                    fontSize: "1.2rem",
                    color: "#fff",
                    margin: "0 auto 4px",
                  }}
                >
                  {defender.name.charAt(0)}
                </div>
                <div style={{ fontWeight: 600, fontSize: "0.85rem", color: defender.color }}>{defender.name}</div>
                {defenderRoll !== undefined && (
                  <div style={{ fontSize: "0.8rem", fontFamily: "monospace" }}>
                    Roll: {defenderRoll} {defenderTotal !== undefined && `(Total: ${defenderTotal})`}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Result */}
          <div style={{ textAlign: "center", marginBottom: 12 }}>
            {tie && (
              <div style={{ color: "#ffcc00", fontSize: "1rem", fontWeight: 700 }}>TIE!</div>
            )}
            {winner && !tie && (
              <div style={{ color: "#00ff88", fontSize: "1rem", fontWeight: 700 }}>
                {winner.name} wins!
              </div>
            )}
            {hit !== undefined && (
              <div style={{ color: hit ? "#ff3355" : "#00ff88", fontSize: "1rem", fontWeight: 700 }}>
                {ducked ? "DUCKED!" : hit ? "HIT!" : "MISSED!"}
              </div>
            )}
            {(damage !== undefined && damage > 0) && (
              <div style={{ color: "#ff3355", fontSize: "0.9rem" }}>
                {damage} damage dealt!
              </div>
            )}
            {(shootDamage !== undefined && shootDamage > 0) && (
              <div style={{ color: "#ff3355", fontSize: "0.9rem" }}>
                {shootDamage} damage dealt!
              </div>
            )}
            {(defenderDied || attackerDied) && (
              <div style={{ color: "#ff3355", fontSize: "1.1rem", fontWeight: 800, marginTop: 4 }}>
                {loser?.name || "Someone"} has been killed!
              </div>
            )}
            {message && (
              <div style={{ color: "#9090b0", fontSize: "0.85rem", marginTop: 4 }}>{message}</div>
            )}
          </div>
        </div>
        <div className="dialog-actions">
          {canContinue && (
            <button className="btn btn-danger" onClick={() => onContinue(true)}>
              Continue Fighting
            </button>
          )}
          <button className="btn btn-primary" onClick={() => onContinue(false)}>
            {canContinue ? "Stop Fighting" : "Close"}
          </button>
        </div>
      </div>
    </div>
  );
}
