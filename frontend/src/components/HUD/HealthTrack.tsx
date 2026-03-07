import type { CharacterState } from "../../api/types";

interface Props {
  players: CharacterState[];
  currentPlayerId?: string;
}

export function HealthTrack({ players, currentPlayerId }: Props) {
  return (
    <div className="panel" style={{ height: "100%" }}>
      <div className="panel-title">Health</div>
      {players.map((player) => {
        const hpPercent = player.max_health > 0
          ? Math.max(0, (player.health / player.max_health) * 100)
          : 0;

        let barColor = player.color;
        if (hpPercent <= 25) barColor = "#ff3355";
        else if (hpPercent <= 50) barColor = "#ff8800";

        const isCurrent = player.id === currentPlayerId;
        const isDead = player.is_permanently_dead;
        const isInVat = player.is_in_bio_vat;

        return (
          <div
            key={player.id}
            className="health-bar-container"
            style={{
              opacity: isDead ? 0.4 : 1,
              borderLeft: isCurrent ? `3px solid ${player.color}` : "3px solid transparent",
              paddingLeft: 4,
            }}
          >
            <div className="health-bar-label">
              <span className="char-name" style={{ color: player.color, fontSize: "0.65rem" }}>
                {player.name.split(" ")[0]}
              </span>
              <span className="hp-text">
                {player.health}/{player.max_health}
              </span>
            </div>
            <div className="health-bar-track">
              <div
                className="health-bar-fill"
                style={{
                  width: `${hpPercent}%`,
                  background: `linear-gradient(90deg, ${barColor}88, ${barColor})`,
                }}
              />
            </div>
            {isDead && (
              <div className="health-status dead">DEAD</div>
            )}
            {isInVat && !isDead && (
              <div className="health-status bio-vat">BIO-VAT</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
