import { useState } from "react";
import type { ActionType, GameState, CharacterState } from "../../api/types";

interface Props {
  availableActions: ActionType[];
  currentPlayer: CharacterState | null;
  gameState: GameState;
  onPick: (cardIds?: string[]) => void;
  onFight: (targetId: string, weaponCardId?: string) => void;
  onShoot: (targetId: string, weaponCardId: string) => void;
  onPush: () => void;
  onHeal: () => void;
  onPass: () => void;
}

interface ActionInfo {
  type: ActionType;
  label: string;
  icon: string;
  tooltip: string;
  color: string;
}

const ACTION_INFO: ActionInfo[] = [
  { type: "pick", label: "Pick Up", icon: "[P]", tooltip: "Pick up face-down cards at your space", color: "#ffcc00" },
  { type: "fight", label: "Fight", icon: "[F]", tooltip: "Melee combat with another character at your space", color: "#ff3355" },
  { type: "shoot", label: "Shoot", icon: "[S]", tooltip: "Ranged attack with a shooting weapon", color: "#ff8800" },
  { type: "push", label: "Push Code", icon: "[C]", tooltip: "Push a code room dial (requires being in a code room)", color: "#aa00ff" },
  { type: "heal", label: "Heal", icon: "[H]", tooltip: "Heal at the Bio-Vat", color: "#00ff88" },
  { type: "pass", label: "Pass", icon: "[--]", tooltip: "Skip your action", color: "#606080" },
  { type: "duck", label: "Duck", icon: "[D]", tooltip: "Attempt to dodge an incoming shot", color: "#00aaff" },
];

export function ActionBar({
  availableActions,
  currentPlayer,
  gameState,
  onPick,
  onFight,
  onShoot,
  onPush,
  onHeal,
  onPass,
}: Props) {
  const [showTargetSelect, setShowTargetSelect] = useState<"fight" | "shoot" | null>(null);
  const [selectedWeapon, setSelectedWeapon] = useState<string>("");

  if (!currentPlayer) return null;

  const availableSet = new Set(availableActions);

  // Find potential fight targets (other characters at the same space)
  const fightTargets = gameState.players.filter(
    (p) => p.id !== currentPlayer.id && p.position === currentPlayer.position && !p.is_permanently_dead && !p.is_in_bio_vat
  );

  // Find potential shoot targets (other characters within weapon range -- simplified, just show all alive non-vat players)
  const shootTargets = gameState.players.filter(
    (p) => p.id !== currentPlayer.id && !p.is_permanently_dead && !p.is_in_bio_vat
  );

  // Weapons in hand
  const meleeWeapons = currentPlayer.hand.filter((c) => c.is_weapon);
  const shootingWeapons = currentPlayer.hand.filter((c) => c.is_shooting_weapon);

  const handleActionClick = (type: ActionType) => {
    switch (type) {
      case "pick":
        onPick();
        break;
      case "fight":
        if (fightTargets.length === 1 && meleeWeapons.length <= 1) {
          onFight(fightTargets[0].id, meleeWeapons[0]?.id);
        } else {
          setShowTargetSelect("fight");
        }
        break;
      case "shoot":
        setShowTargetSelect("shoot");
        break;
      case "push":
        onPush();
        break;
      case "heal":
        onHeal();
        break;
      case "pass":
        onPass();
        break;
      default:
        break;
    }
  };

  const handleTargetConfirm = (targetId: string) => {
    if (showTargetSelect === "fight") {
      onFight(targetId, selectedWeapon || undefined);
    } else if (showTargetSelect === "shoot") {
      if (!selectedWeapon) return;
      onShoot(targetId, selectedWeapon);
    }
    setShowTargetSelect(null);
    setSelectedWeapon("");
  };

  return (
    <>
      <div className="action-bar">
        <span className="action-label">Actions:</span>
        {ACTION_INFO.filter((a) => availableSet.has(a.type)).map((action) => (
          <div key={action.type} className="tooltip-wrapper">
            <button
              className="btn"
              style={{ borderColor: action.color, color: action.color }}
              onClick={() => handleActionClick(action.type)}
            >
              <span>{action.icon}</span>
              <span>{action.label}</span>
            </button>
            <span className="tooltip-text">{action.tooltip}</span>
          </div>
        ))}
        {availableActions.length === 0 && (
          <span style={{ color: "#606080", fontSize: "0.8rem" }}>No actions available</span>
        )}
      </div>

      {/* Target selection overlay */}
      {showTargetSelect && (
        <div className="dialog-overlay" onClick={() => { setShowTargetSelect(null); setSelectedWeapon(""); }}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-title">
              {showTargetSelect === "fight" ? "Choose Fight Target" : "Choose Shoot Target"}
            </div>
            <div className="dialog-body">
              {/* Weapon selection */}
              {showTargetSelect === "fight" && meleeWeapons.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: "0.8rem", color: "#9090b0", marginBottom: 4 }}>
                    Select weapon (optional):
                  </div>
                  <select
                    value={selectedWeapon}
                    onChange={(e) => setSelectedWeapon(e.target.value)}
                    style={{
                      background: "#111128",
                      border: "1px solid #2a2a4a",
                      color: "#e0e0e0",
                      padding: "4px 8px",
                      borderRadius: 4,
                      width: "100%",
                    }}
                  >
                    <option value="">Bare hands</option>
                    {meleeWeapons.map((w) => (
                      <option key={w.id} value={w.id}>{w.name} (+{w.combat_bonus})</option>
                    ))}
                  </select>
                </div>
              )}
              {showTargetSelect === "shoot" && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: "0.8rem", color: "#9090b0", marginBottom: 4 }}>
                    Select shooting weapon:
                  </div>
                  <select
                    value={selectedWeapon}
                    onChange={(e) => setSelectedWeapon(e.target.value)}
                    style={{
                      background: "#111128",
                      border: "1px solid #2a2a4a",
                      color: "#e0e0e0",
                      padding: "4px 8px",
                      borderRadius: 4,
                      width: "100%",
                    }}
                  >
                    <option value="">-- Select --</option>
                    {shootingWeapons.map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.name} ({w.damage_dice}d6{w.damage_bonus ? `+${w.damage_bonus}` : ""}, range {w.weapon_range})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Target list */}
              <div style={{ fontSize: "0.8rem", color: "#9090b0", marginBottom: 4 }}>
                Select target:
              </div>
              {(showTargetSelect === "fight" ? fightTargets : shootTargets).map((target) => (
                <div
                  key={target.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "6px 8px",
                    background: "#1a1a3a",
                    borderRadius: 4,
                    marginBottom: 4,
                    cursor: showTargetSelect === "shoot" && !selectedWeapon ? "not-allowed" : "pointer",
                    opacity: showTargetSelect === "shoot" && !selectedWeapon ? 0.5 : 1,
                  }}
                  onClick={() => {
                    if (showTargetSelect === "shoot" && !selectedWeapon) return;
                    handleTargetConfirm(target.id);
                  }}
                >
                  <div
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: "50%",
                      backgroundColor: target.color,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: 700,
                      fontSize: "0.75rem",
                      color: "#fff",
                    }}
                  >
                    {target.name.charAt(0)}
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>{target.name}</div>
                    <div style={{ fontSize: "0.7rem", color: "#9090b0" }}>
                      HP: {target.health}/{target.max_health} | Pos: {target.position}
                    </div>
                  </div>
                </div>
              ))}
              {(showTargetSelect === "fight" ? fightTargets : shootTargets).length === 0 && (
                <p style={{ color: "#606080", fontSize: "0.8rem" }}>No valid targets</p>
              )}
            </div>
            <div className="dialog-actions">
              <button className="btn" onClick={() => { setShowTargetSelect(null); setSelectedWeapon(""); }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
