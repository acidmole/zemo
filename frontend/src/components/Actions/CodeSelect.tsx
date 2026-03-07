import type { GameState } from "../../api/types";

interface Props {
  gameState: GameState;
  onPush: (codeValue?: "A" | "B") => void;
  onClose: () => void;
}

export function CodeSelect({ gameState, onClose, onPush }: Props) {
  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-title">
          Push Code Room Dial
        </div>
        <div className="dialog-body">
          {/* Show current code room states */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: "0.85rem", color: "#9090b0", marginBottom: 8 }}>
              Current Code Room States:
            </div>
            <div style={{ display: "flex", justifyContent: "center", gap: 16 }}>
              {gameState.code_rooms.map((cr) => {
                const value = cr.value === "UNSET" ? "?" : cr.value;
                const color = cr.value === "A" ? "#00ff88" : cr.value === "B" ? "#ff3355" : "#ffcc00";
                return (
                  <div
                    key={cr.room_number}
                    style={{
                      textAlign: "center",
                      padding: "8px 16px",
                      background: "#1a1a3a",
                      borderRadius: 6,
                      border: `1px solid ${color}`,
                    }}
                  >
                    <div style={{ fontSize: "0.75rem", color: "#9090b0" }}>Room {cr.room_number}</div>
                    <div style={{ fontSize: "1.6rem", fontWeight: 800, color, fontFamily: "monospace" }}>
                      {value}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ textAlign: "center", marginBottom: 12 }}>
            <p style={{ fontSize: "0.8rem", color: "#9090b0" }}>
              You will roll to push the dial. On success, choose A or B.
              Having a Pod ATM Card gives +3 to your roll.
            </p>
          </div>

          <div style={{ textAlign: "center", marginBottom: 12 }}>
            <div style={{ fontSize: "0.85rem", color: "#aa00ff", fontWeight: 700, marginBottom: 8 }}>
              Choose the value to set (the server will determine success):
            </div>
            <div style={{ display: "flex", justifyContent: "center", gap: 12 }}>
              <button
                className="btn btn-success btn-lg"
                onClick={() => onPush("A")}
                style={{ minWidth: 80, fontSize: "1.2rem", fontWeight: 800 }}
              >
                A
              </button>
              <button
                className="btn btn-danger btn-lg"
                onClick={() => onPush("B")}
                style={{ minWidth: 80, fontSize: "1.2rem", fontWeight: 800 }}
              >
                B
              </button>
            </div>
          </div>
        </div>
        <div className="dialog-actions">
          <button className="btn" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
