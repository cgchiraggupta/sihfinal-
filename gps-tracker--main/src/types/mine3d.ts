export interface Vector3D {
  x: number;
  y: number;
  z: number;
}

export interface MineNode {
  id: string;
  position: Vector3D;
  label?: string;
  type: 'junction' | 'end' | 'entry' | 'shaft_entry';
}

export interface MineTunnel {
  id: string;
  startNodeId: string;
  endNodeId: string;
  type: 'main_shaft' | 'level_tunnel' | 'ramp' | 'crosscut';
  width?: number;
}

export interface MineLevel {
  id: string;
  depth: number;
  name: string;
  color: string;
}

export interface MineLayout {
  nodes: MineNode[];
  tunnels: MineTunnel[];
  levels: MineLevel[];
  centerReference: {
    lat: number;
    lng: number;
  };
}

export type ViewMode = '2d' | '3d';

