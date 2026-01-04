// Predefined Mine Tunnel Data
// This represents a realistic underground mine layout for 3D visualization

import { MineData3D, TunnelSegment, MineLevel, MineStation, ShaftData, RampData, Point3D } from '@/types/mine3d';

// Helper function to create tunnel segments
const createTunnel = (
  id: string,
  name: string,
  type: TunnelSegment['type'],
  level: number,
  start: Point3D,
  end: Point3D,
  width: number = 5,
  height: number = 4
): TunnelSegment => ({
  id,
  name,
  type,
  level,
  startPoint: start,
  endPoint: end,
  width,
  height,
  isActive: true,
  hasVentilation: true,
  hasRailTrack: type === 'main_tunnel' || type === 'extraction',
});

// Helper function to create stations
const createStation = (
  id: string,
  name: string,
  type: MineStation['type'],
  position: Point3D,
  isOperational: boolean = true
): MineStation => ({
  id,
  name,
  type,
  position,
  isOperational,
});

// ============================================
// LEVEL 1: -50 meters (Upper Level)
// ============================================
const level1Tunnels: TunnelSegment[] = [
  // Main access tunnel from shaft
  createTunnel('l1-main-1', 'Main Access L1', 'main_tunnel', -1, 
    { x: 0, y: -50, z: 0 }, { x: 80, y: -50, z: 0 }, 6, 5),
  
  // Branch tunnels
  createTunnel('l1-branch-1', 'North Branch L1', 'access_tunnel', -1,
    { x: 40, y: -50, z: 0 }, { x: 40, y: -50, z: 60 }, 5, 4),
  createTunnel('l1-branch-2', 'South Branch L1', 'access_tunnel', -1,
    { x: 40, y: -50, z: 0 }, { x: 40, y: -50, z: -50 }, 5, 4),
  
  // Extraction areas
  createTunnel('l1-ext-1', 'Extraction Zone A1', 'extraction', -1,
    { x: 80, y: -50, z: 0 }, { x: 120, y: -50, z: 20 }, 4, 3.5),
  createTunnel('l1-ext-2', 'Extraction Zone A2', 'extraction', -1,
    { x: 80, y: -50, z: 0 }, { x: 110, y: -50, z: -30 }, 4, 3.5),
  
  // Ventilation tunnel
  createTunnel('l1-vent-1', 'Ventilation L1', 'ventilation', -1,
    { x: 40, y: -50, z: 60 }, { x: 60, y: -50, z: 80 }, 3, 3),
  
  // Crosscuts
  createTunnel('l1-cross-1', 'Crosscut L1-A', 'crosscut', -1,
    { x: 60, y: -50, z: -20 }, { x: 60, y: -50, z: 20 }, 4, 3.5),
];

const level1Stations: MineStation[] = [
  createStation('l1-station-1', 'Loading Bay L1', 'loading', { x: 80, y: -50, z: 0 }),
  createStation('l1-station-2', 'Refuge Chamber L1', 'refuge', { x: 40, y: -50, z: 30 }),
  createStation('l1-station-3', 'Emergency Exit L1', 'emergency_exit', { x: 60, y: -50, z: 80 }),
];

// ============================================
// LEVEL 2: -100 meters (Middle Level)
// ============================================
const level2Tunnels: TunnelSegment[] = [
  // Main access from ramp
  createTunnel('l2-main-1', 'Main Access L2', 'main_tunnel', -2,
    { x: 0, y: -100, z: 0 }, { x: 100, y: -100, z: 0 }, 6, 5),
  
  // Extended main tunnel
  createTunnel('l2-main-2', 'Main Haulage L2', 'main_tunnel', -2,
    { x: 100, y: -100, z: 0 }, { x: 160, y: -100, z: 0 }, 6, 5),
  
  // Branch tunnels
  createTunnel('l2-branch-1', 'North Branch L2', 'access_tunnel', -2,
    { x: 50, y: -100, z: 0 }, { x: 50, y: -100, z: 80 }, 5, 4),
  createTunnel('l2-branch-2', 'South Branch L2', 'access_tunnel', -2,
    { x: 50, y: -100, z: 0 }, { x: 50, y: -100, z: -70 }, 5, 4),
  createTunnel('l2-branch-3', 'East Branch L2', 'access_tunnel', -2,
    { x: 100, y: -100, z: 0 }, { x: 100, y: -100, z: 50 }, 5, 4),
  
  // Extraction zones
  createTunnel('l2-ext-1', 'Extraction Zone B1', 'extraction', -2,
    { x: 50, y: -100, z: 80 }, { x: 90, y: -100, z: 100 }, 4, 3.5),
  createTunnel('l2-ext-2', 'Extraction Zone B2', 'extraction', -2,
    { x: 50, y: -100, z: 80 }, { x: 30, y: -100, z: 110 }, 4, 3.5),
  createTunnel('l2-ext-3', 'Extraction Zone B3', 'extraction', -2,
    { x: 160, y: -100, z: 0 }, { x: 180, y: -100, z: 30 }, 4, 3.5),
  createTunnel('l2-ext-4', 'Extraction Zone B4', 'extraction', -2,
    { x: 160, y: -100, z: 0 }, { x: 190, y: -100, z: -20 }, 4, 3.5),
  
  // Crosscuts connecting branches
  createTunnel('l2-cross-1', 'Crosscut L2-A', 'crosscut', -2,
    { x: 70, y: -100, z: -40 }, { x: 70, y: -100, z: 40 }, 4, 3.5),
  createTunnel('l2-cross-2', 'Crosscut L2-B', 'crosscut', -2,
    { x: 130, y: -100, z: -30 }, { x: 130, y: -100, z: 30 }, 4, 3.5),
  
  // Ventilation
  createTunnel('l2-vent-1', 'Ventilation L2 North', 'ventilation', -2,
    { x: 30, y: -100, z: 110 }, { x: 10, y: -100, z: 130 }, 3, 3),
];

const level2Stations: MineStation[] = [
  createStation('l2-station-1', 'Main Loading L2', 'loading', { x: 100, y: -100, z: 0 }),
  createStation('l2-station-2', 'Secondary Loading L2', 'loading', { x: 160, y: -100, z: 0 }),
  createStation('l2-station-3', 'Refuge Chamber L2-A', 'refuge', { x: 50, y: -100, z: 40 }),
  createStation('l2-station-4', 'Refuge Chamber L2-B', 'refuge', { x: 130, y: -100, z: 0 }),
  createStation('l2-station-5', 'Maintenance Bay L2', 'maintenance', { x: 0, y: -100, z: 0 }),
  createStation('l2-station-6', 'Pump Station L2', 'pump', { x: 50, y: -100, z: -70 }),
];

// ============================================
// LEVEL 3: -150 meters (Lower Level)
// ============================================
const level3Tunnels: TunnelSegment[] = [
  // Main access
  createTunnel('l3-main-1', 'Main Access L3', 'main_tunnel', -3,
    { x: 0, y: -150, z: 0 }, { x: 120, y: -150, z: 0 }, 6, 5),
  
  // Extended network
  createTunnel('l3-main-2', 'Main Haulage L3', 'main_tunnel', -3,
    { x: 120, y: -150, z: 0 }, { x: 200, y: -150, z: 0 }, 6, 5),
  
  // Branch tunnels - more extensive at this level
  createTunnel('l3-branch-1', 'North Branch L3', 'access_tunnel', -3,
    { x: 60, y: -150, z: 0 }, { x: 60, y: -150, z: 100 }, 5, 4),
  createTunnel('l3-branch-2', 'South Branch L3', 'access_tunnel', -3,
    { x: 60, y: -150, z: 0 }, { x: 60, y: -150, z: -90 }, 5, 4),
  createTunnel('l3-branch-3', 'North Branch L3-B', 'access_tunnel', -3,
    { x: 140, y: -150, z: 0 }, { x: 140, y: -150, z: 70 }, 5, 4),
  createTunnel('l3-branch-4', 'South Branch L3-B', 'access_tunnel', -3,
    { x: 140, y: -150, z: 0 }, { x: 140, y: -150, z: -60 }, 5, 4),
  
  // Extraction zones - richest at this level
  createTunnel('l3-ext-1', 'Extraction Zone C1', 'extraction', -3,
    { x: 60, y: -150, z: 100 }, { x: 100, y: -150, z: 120 }, 4, 3.5),
  createTunnel('l3-ext-2', 'Extraction Zone C2', 'extraction', -3,
    { x: 60, y: -150, z: 100 }, { x: 40, y: -150, z: 130 }, 4, 3.5),
  createTunnel('l3-ext-3', 'Extraction Zone C3', 'extraction', -3,
    { x: 60, y: -150, z: -90 }, { x: 90, y: -150, z: -110 }, 4, 3.5),
  createTunnel('l3-ext-4', 'Extraction Zone C4', 'extraction', -3,
    { x: 200, y: -150, z: 0 }, { x: 230, y: -150, z: 30 }, 4, 3.5),
  createTunnel('l3-ext-5', 'Extraction Zone C5', 'extraction', -3,
    { x: 200, y: -150, z: 0 }, { x: 220, y: -150, z: -40 }, 4, 3.5),
  createTunnel('l3-ext-6', 'Extraction Zone C6', 'extraction', -3,
    { x: 140, y: -150, z: 70 }, { x: 170, y: -150, z: 90 }, 4, 3.5),
  
  // Crosscuts
  createTunnel('l3-cross-1', 'Crosscut L3-A', 'crosscut', -3,
    { x: 90, y: -150, z: -50 }, { x: 90, y: -150, z: 50 }, 4, 3.5),
  createTunnel('l3-cross-2', 'Crosscut L3-B', 'crosscut', -3,
    { x: 170, y: -150, z: -40 }, { x: 170, y: -150, z: 40 }, 4, 3.5),
  
  // Ventilation network
  createTunnel('l3-vent-1', 'Ventilation L3', 'ventilation', -3,
    { x: 40, y: -150, z: 130 }, { x: 20, y: -150, z: 150 }, 3, 3),
];

const level3Stations: MineStation[] = [
  createStation('l3-station-1', 'Main Loading L3', 'loading', { x: 120, y: -150, z: 0 }),
  createStation('l3-station-2', 'Ore Pass L3', 'loading', { x: 200, y: -150, z: 0 }),
  createStation('l3-station-3', 'Refuge Chamber L3-A', 'refuge', { x: 60, y: -150, z: 50 }),
  createStation('l3-station-4', 'Refuge Chamber L3-B', 'refuge', { x: 170, y: -150, z: 0 }),
  createStation('l3-station-5', 'Maintenance L3', 'maintenance', { x: 0, y: -150, z: 0 }),
  createStation('l3-station-6', 'Emergency Exit L3', 'emergency_exit', { x: 20, y: -150, z: 150 }),
];

// ============================================
// LEVEL 4: -200 meters (Deep Level)
// ============================================
const level4Tunnels: TunnelSegment[] = [
  // Main access
  createTunnel('l4-main-1', 'Main Access L4', 'main_tunnel', -4,
    { x: 0, y: -200, z: 0 }, { x: 80, y: -200, z: 0 }, 6, 5),
  
  // Development heading
  createTunnel('l4-main-2', 'Development Heading L4', 'main_tunnel', -4,
    { x: 80, y: -200, z: 0 }, { x: 150, y: -200, z: 0 }, 5, 4.5),
  
  // Branch tunnels
  createTunnel('l4-branch-1', 'North Heading L4', 'access_tunnel', -4,
    { x: 80, y: -200, z: 0 }, { x: 80, y: -200, z: 60 }, 5, 4),
  createTunnel('l4-branch-2', 'South Heading L4', 'access_tunnel', -4,
    { x: 80, y: -200, z: 0 }, { x: 80, y: -200, z: -50 }, 5, 4),
  
  // Active extraction (newest)
  createTunnel('l4-ext-1', 'Active Face L4-A', 'extraction', -4,
    { x: 150, y: -200, z: 0 }, { x: 180, y: -200, z: 20 }, 4, 3.5),
  createTunnel('l4-ext-2', 'Active Face L4-B', 'extraction', -4,
    { x: 80, y: -200, z: 60 }, { x: 110, y: -200, z: 80 }, 4, 3.5),
];

const level4Stations: MineStation[] = [
  createStation('l4-station-1', 'Loading Point L4', 'loading', { x: 80, y: -200, z: 0 }),
  createStation('l4-station-2', 'Refuge Chamber L4', 'refuge', { x: 40, y: -200, z: 0 }),
];

// ============================================
// SHAFTS (Vertical connections)
// ============================================
const shafts: ShaftData[] = [
  {
    id: 'shaft-main',
    name: 'Main Production Shaft',
    type: 'main',
    topPoint: { x: 0, y: 0, z: 0 },
    bottomPoint: { x: 0, y: -200, z: 0 },
    diameter: 8,
    hasElevator: true,
    hasLadder: true,
  },
  {
    id: 'shaft-vent',
    name: 'Ventilation Shaft',
    type: 'ventilation',
    topPoint: { x: 20, y: 0, z: 150 },
    bottomPoint: { x: 20, y: -150, z: 150 },
    diameter: 5,
    hasElevator: false,
    hasLadder: true,
  },
  {
    id: 'shaft-service',
    name: 'Service Shaft',
    type: 'service',
    topPoint: { x: -20, y: 0, z: 0 },
    bottomPoint: { x: -20, y: -150, z: 0 },
    diameter: 4,
    hasElevator: true,
    hasLadder: true,
  },
];

// ============================================
// RAMPS (Spiral/Decline connections)
// ============================================
const ramps: RampData[] = [
  {
    id: 'ramp-main',
    name: 'Main Decline Ramp',
    points: [
      { x: 0, y: 0, z: 0 },
      { x: -20, y: -25, z: 20 },
      { x: -10, y: -50, z: 40 },
      { x: 10, y: -75, z: 30 },
      { x: 0, y: -100, z: 10 },
      { x: -15, y: -125, z: -10 },
      { x: 0, y: -150, z: 0 },
      { x: 10, y: -175, z: 10 },
      { x: 0, y: -200, z: 0 },
    ],
    width: 6,
    gradient: 12,
    isMainAccess: true,
  },
];

// ============================================
// MINE LEVELS ASSEMBLY
// ============================================
const mineLevels: MineLevel[] = [
  {
    id: 'level-1',
    name: 'Level 1 - Upper',
    depth: -50,
    color: '#0ea5e9',
    tunnels: level1Tunnels,
    stations: level1Stations,
  },
  {
    id: 'level-2',
    name: 'Level 2 - Middle',
    depth: -100,
    color: '#8b5cf6',
    tunnels: level2Tunnels,
    stations: level2Stations,
  },
  {
    id: 'level-3',
    name: 'Level 3 - Lower',
    depth: -150,
    color: '#f59e0b',
    tunnels: level3Tunnels,
    stations: level3Stations,
  },
  {
    id: 'level-4',
    name: 'Level 4 - Deep',
    depth: -200,
    color: '#ef4444',
    tunnels: level4Tunnels,
    stations: level4Stations,
  },
];

// ============================================
// COMPLETE MINE DATA EXPORT
// ============================================
export const MINE_DATA: MineData3D = {
  id: 'mine-001',
  name: 'Underground Mining Complex',
  location: {
    latitude: 22.292675,
    longitude: 73.366018,
  },
  totalDepth: 200,
  levels: mineLevels,
  shafts,
  ramps,
};

// Helper function to get all tunnels across all levels
export const getAllTunnels = (): TunnelSegment[] => {
  return MINE_DATA.levels.flatMap(level => level.tunnels);
};

// Helper function to get all stations across all levels
export const getAllStations = (): MineStation[] => {
  return MINE_DATA.levels.flatMap(level => level.stations);
};

// Helper function to get tunnels at a specific depth
export const getTunnelsAtDepth = (depth: number): TunnelSegment[] => {
  const level = MINE_DATA.levels.find(l => l.depth === depth);
  return level?.tunnels || [];
};

// Helper function to find nearest refuge chamber
export const findNearestRefuge = (position: Point3D): MineStation | null => {
  const refuges = getAllStations().filter(s => s.type === 'refuge');
  if (refuges.length === 0) return null;
  
  let nearest = refuges[0];
  let minDistance = Infinity;
  
  refuges.forEach(refuge => {
    const distance = Math.sqrt(
      Math.pow(refuge.position.x - position.x, 2) +
      Math.pow(refuge.position.y - position.y, 2) +
      Math.pow(refuge.position.z - position.z, 2)
    );
    if (distance < minDistance) {
      minDistance = distance;
      nearest = refuge;
    }
  });
  
  return nearest;
};

// Convert GPS position to 3D mine coordinates
export const gpsTo3D = (
  lat: number, 
  lng: number, 
  depth: number,
  baseLat: number = MINE_DATA.location.latitude,
  baseLng: number = MINE_DATA.location.longitude,
  scale: number = 10000 // meters per degree approximation
): Point3D => {
  return {
    x: (lng - baseLng) * scale,
    y: -Math.abs(depth), // Negative for underground
    z: (lat - baseLat) * scale,
  };
};

// Convert 3D mine coordinates to GPS
export const threeDToGps = (
  point: Point3D,
  baseLat: number = MINE_DATA.location.latitude,
  baseLng: number = MINE_DATA.location.longitude,
  scale: number = 10000
): { lat: number; lng: number; depth: number } => {
  return {
    lat: baseLat + (point.z / scale),
    lng: baseLng + (point.x / scale),
    depth: Math.abs(point.y),
  };
};

export default MINE_DATA;

