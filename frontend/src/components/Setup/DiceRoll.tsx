import { useState, useEffect, useCallback } from "react";

interface Props {
  value: number | null;
  onRollComplete?: () => void;
  rolling?: boolean;
}

export function DiceRoll({ value, rolling = false }: Props) {
  const [displayValue, setDisplayValue] = useState<number | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);

  const animate = useCallback(() => {
    if (value === null) return;
    setIsAnimating(true);
    let ticks = 0;
    const maxTicks = 12;
    const interval = setInterval(() => {
      ticks++;
      setDisplayValue(Math.floor(Math.random() * 6) + 1 + Math.floor(Math.random() * 6) + 1);
      if (ticks >= maxTicks) {
        clearInterval(interval);
        setDisplayValue(value);
        setIsAnimating(false);
      }
    }, 80);
    return () => clearInterval(interval);
  }, [value]);

  useEffect(() => {
    if (value !== null && rolling) {
      const cleanup = animate();
      return cleanup;
    } else if (value !== null) {
      setDisplayValue(value);
    } else {
      setDisplayValue(null);
    }
  }, [value, rolling, animate]);

  if (displayValue === null) return null;

  // Split into two dice (approximate)
  const die1 = Math.min(6, Math.max(1, Math.ceil(displayValue / 2)));
  const die2 = displayValue - die1;

  return (
    <div className="dice-container">
      <div className={`dice ${isAnimating ? "rolling" : ""}`}>
        {die1}
      </div>
      <div className={`dice ${isAnimating ? "rolling" : ""}`}>
        {Math.max(1, die2)}
      </div>
      <span style={{ fontSize: "0.8rem", color: "#9090b0", marginLeft: 4 }}>
        = {displayValue}
      </span>
    </div>
  );
}
