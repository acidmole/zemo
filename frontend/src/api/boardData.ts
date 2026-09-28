/**
 * Static setup data: character templates and escape codes.
 */

// Character template data for setup screen
export interface CharacterTemplate {
  id: string;
  name: string;
  maxHealth: number;
  movementMod: number;
  combatMod: number;
  capacity: number;
  actionsPerTurn: number;
  special: string;
  color: string;
  description: string;
}

export const CHARACTER_TEMPLATES: CharacterTemplate[] = [
  {
    id: "chuckie",
    name: "Chuckie the Zombie",
    maxHealth: 20,
    movementMod: 0,
    combatMod: 2,
    capacity: 5,
    actionsPerTurn: 1,
    special: "Exploding Polyps",
    color: "#4CAF50",
    description: "A tough zombie with +2 combat bonus and 20 HP. Special: Exploding Polyps.",
  },
  {
    id: "floyd",
    name: "Floyd the Droid",
    maxHealth: 18,
    movementMod: 0,
    combatMod: 0,
    capacity: 5,
    actionsPerTurn: 1,
    special: "Transformer Chassis",
    color: "#2196F3",
    description: "A versatile droid with 18 HP. Special: Transformer Chassis.",
  },
  {
    id: "mush",
    name: "Mush the Abomination",
    maxHealth: 19,
    movementMod: 0,
    combatMod: 2,
    capacity: 5,
    actionsPerTurn: 1,
    special: "Der Blinkenteleporten",
    color: "#9C27B0",
    description: "An abomination with +2 combat and 19 HP. Special: Der Blinkenteleporten.",
  },
  {
    id: "pete",
    name: "Pete the Cook",
    maxHealth: 13,
    movementMod: 0,
    combatMod: 0,
    capacity: 5,
    actionsPerTurn: 2,
    special: "Commando Training",
    color: "#FF9800",
    description: "A nimble cook with 2 actions per turn but only 13 HP. Special: Commando Training.",
  },
  {
    id: "rats",
    name: "The Rats",
    maxHealth: 9,
    movementMod: 0,
    combatMod: 0,
    capacity: 5,
    actionsPerTurn: 1,
    special: "Rat Packs",
    color: "#795548",
    description: "Sneaky rats with only 9 HP but unique abilities. Special: Rat Packs.",
  },
];

export const ESCAPE_CODES = [
  "AAA", "AAB", "ABA", "ABB",
  "BAA", "BAB", "BBA", "BBB",
];
