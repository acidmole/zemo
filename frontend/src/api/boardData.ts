/**
 * Board layout data for SVG rendering.
 * Mirrors the backend board_layout.py but with pixel coordinates for the SVG board.
 */

export interface SpacePosition {
  id: string;
  x: number;
  y: number;
  type: "hallway" | "room" | "code_room" | "escape_pod" | "bio_vat" | "airlock";
  name: string;
}

export interface Edge {
  from: string;
  to: string;
}

// Room names matching backend
const ROOM_NAMES: Record<string, string> = {
  "7": "Reactor Room",
  "11": "Security",
  "13": "The Brig",
  "17": "The Armory",
  "21": "Vending Machines",
  "22": "Lavatory",
  "23": "Lost and Found",
  "25": "Casino",
  "26": "The Zemo Zoo",
  "29": "Kitchen",
  "32": "Command Control",
  code_room_1: "Code Room 1",
  code_room_2: "Code Room 2",
  code_room_3: "Code Room 3",
  escape_pod: "Escape Pod",
  bio_vat: "Bio-Vat",
  airlock: "Airlock",
};

const ROOM_SPACE_IDS = new Set([
  "7", "11", "13", "17", "21", "22", "23", "25", "26", "29", "32",
]);

function getSpaceType(id: string): SpacePosition["type"] {
  if (id.startsWith("code_room")) return "code_room";
  if (id === "escape_pod") return "escape_pod";
  if (id === "bio_vat") return "bio_vat";
  if (id === "airlock") return "airlock";
  if (ROOM_SPACE_IDS.has(id)) return "room";
  return "hallway";
}

function buildSpaces(): SpacePosition[] {
  const spaces: SpacePosition[] = [];

  // Top row: spaces 1-9, y=80, x from 60 to 860
  for (let i = 0; i < 9; i++) {
    const sid = String(i + 1);
    spaces.push({
      id: sid,
      x: 60 + i * 100,
      y: 80,
      type: getSpaceType(sid),
      name: ROOM_NAMES[sid] || `Space ${sid}`,
    });
  }

  // Right column: spaces 10-16, x=860, y from 180 to 780
  for (let i = 0; i < 7; i++) {
    const sid = String(10 + i);
    spaces.push({
      id: sid,
      x: 860,
      y: 180 + i * 100,
      type: getSpaceType(sid),
      name: ROOM_NAMES[sid] || `Space ${sid}`,
    });
  }

  // Bottom row: spaces 17-24, y=780, x from 760 to 60
  for (let i = 0; i < 8; i++) {
    const sid = String(17 + i);
    spaces.push({
      id: sid,
      x: 760 - i * 100,
      y: 780,
      type: getSpaceType(sid),
      name: ROOM_NAMES[sid] || `Space ${sid}`,
    });
  }

  // Left column: spaces 25-32, x=60, y from 680 to 180
  for (let i = 0; i < 8; i++) {
    const sid = String(25 + i);
    spaces.push({
      id: sid,
      x: 60,
      y: 680 - i * (500 / 7),
      type: getSpaceType(sid),
      name: ROOM_NAMES[sid] || `Space ${sid}`,
    });
  }

  // Special interior spaces
  spaces.push({
    id: "code_room_1",
    x: 300,
    y: 200,
    type: "code_room",
    name: "Code Room 1",
  });
  spaces.push({
    id: "code_room_2",
    x: 160,
    y: 130,
    type: "code_room",
    name: "Code Room 2",
  });
  spaces.push({
    id: "code_room_3",
    x: 700,
    y: 680,
    type: "code_room",
    name: "Code Room 3",
  });
  spaces.push({
    id: "escape_pod",
    x: 460,
    y: 430,
    type: "escape_pod",
    name: "Escape Pod",
  });
  spaces.push({
    id: "bio_vat",
    x: 460,
    y: 250,
    type: "bio_vat",
    name: "Bio-Vat",
  });
  spaces.push({
    id: "airlock",
    x: 460,
    y: 600,
    type: "airlock",
    name: "Airlock",
  });

  return spaces;
}

function buildEdges(): Edge[] {
  const edges: Edge[] = [];

  // Perimeter loop: 1-2, 2-3, ..., 31-32, 32-1
  for (let i = 1; i <= 32; i++) {
    const next = i === 32 ? 1 : i + 1;
    edges.push({ from: String(i), to: String(next) });
  }

  // Special space connections
  edges.push({ from: "code_room_1", to: "3" });
  edges.push({ from: "code_room_1", to: "4" });
  edges.push({ from: "code_room_2", to: "1" });
  edges.push({ from: "code_room_2", to: "32" });
  edges.push({ from: "code_room_3", to: "15" });
  edges.push({ from: "code_room_3", to: "16" });
  edges.push({ from: "escape_pod", to: "5" });
  edges.push({ from: "escape_pod", to: "12" });
  edges.push({ from: "escape_pod", to: "20" });
  edges.push({ from: "escape_pod", to: "28" });
  edges.push({ from: "bio_vat", to: "6" });
  edges.push({ from: "airlock", to: "19" });

  return edges;
}

export const BOARD_SPACES: SpacePosition[] = buildSpaces();
export const BOARD_EDGES: Edge[] = buildEdges();

// Quick lookup by space ID
export const SPACE_MAP: Record<string, SpacePosition> = {};
for (const space of BOARD_SPACES) {
  SPACE_MAP[space.id] = space;
}

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
