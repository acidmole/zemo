import { DiceRoll } from "../Setup/DiceRoll";

interface Props {
  roll: number | null;
  reachableCount: number;
  onRoll: () => void;
  onStay: () => void;
  hasRolled: boolean;
  hasMoved: boolean;
}

export function MovementUI({ roll, reachableCount, onRoll, onStay, hasRolled, hasMoved }: Props) {
  if (hasMoved) {
    return (
      <div className="movement-ui">
        <span style={{ color: "#00ff88", fontSize: "0.85rem" }}>
          Movement complete. Transitioning to action phase...
        </span>
      </div>
    );
  }

  return (
    <div className="movement-ui">
      {!hasRolled && (
        <>
          <span className="movement-hint">Roll dice to move</span>
          <button className="btn btn-primary" onClick={onRoll}>
            Roll Dice
          </button>
        </>
      )}

      {hasRolled && roll !== null && (
        <>
          <DiceRoll value={roll} rolling={true} />
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
            <span className="movement-hint">
              {reachableCount > 0
                ? `Click a highlighted space to move (${reachableCount} reachable)`
                : "No reachable spaces"}
            </span>
          </div>
          <button className="btn" onClick={onStay}>
            Stay Here
          </button>
        </>
      )}
    </div>
  );
}
