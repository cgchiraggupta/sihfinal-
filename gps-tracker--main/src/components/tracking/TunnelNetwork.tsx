// TunnelNetwork.tsx - Renders the 3D tunnel network with wireframe and solid options
import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Tube, Text, Sphere } from '@react-three/drei';
import * as THREE from 'three';
import { TunnelSegment, MineStation, ShaftData, RampData, MINE_COLORS, Point3D } from '@/types/mine3d';

interface TunnelNetworkProps {
  tunnels: TunnelSegment[];
  stations: MineStation[];
  shafts: ShaftData[];
  ramps: RampData[];
  showWireframe: boolean;
  showSolidTunnels: boolean;
  showLabels: boolean;
  selectedLevel: number | null;
  scale?: number;
}

// Get color based on tunnel type
const getTunnelColor = (type: TunnelSegment['type']): string => {
  switch (type) {
    case 'main_tunnel': return MINE_COLORS.mainTunnel;
    case 'access_tunnel': return MINE_COLORS.accessTunnel;
    case 'ventilation': return MINE_COLORS.ventilation;
    case 'extraction': return MINE_COLORS.extraction;
    case 'shaft': return MINE_COLORS.shaft;
    case 'crosscut': return MINE_COLORS.crosscut;
    case 'ramp': return MINE_COLORS.ramp;
    default: return '#ffffff';
  }
};

// Get color based on station type
const getStationColor = (type: MineStation['type']): string => {
  switch (type) {
    case 'loading': return MINE_COLORS.loading;
    case 'refuge': return MINE_COLORS.refuge;
    case 'maintenance': return MINE_COLORS.maintenance;
    case 'emergency_exit': return MINE_COLORS.emergency;
    default: return '#ffffff';
  }
};

// Custom line component using native Three.js
const CustomLine = ({ 
  points, 
  color, 
  lineWidth = 2,
  opacity = 1,
  dashed = false,
}: { 
  points: THREE.Vector3[]; 
  color: string; 
  lineWidth?: number;
  opacity?: number;
  dashed?: boolean;
}) => {
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry().setFromPoints(points);
    return geo;
  }, [points]);

  return (
    <line geometry={geometry}>
      <lineBasicMaterial 
        color={color} 
        transparent={opacity < 1}
        opacity={opacity}
        linewidth={lineWidth}
      />
    </line>
  );
};

// Single tunnel segment component
const TunnelSegmentMesh = ({ 
  tunnel, 
  showWireframe, 
  showSolid,
  showLabel,
  scale = 1 
}: { 
  tunnel: TunnelSegment; 
  showWireframe: boolean; 
  showSolid: boolean;
  showLabel: boolean;
  scale?: number;
}) => {
  const color = getTunnelColor(tunnel.type);
  
  // Create points for the tunnel path
  const points = useMemo(() => [
    new THREE.Vector3(
      tunnel.startPoint.x * scale,
      tunnel.startPoint.y * scale,
      tunnel.startPoint.z * scale
    ),
    new THREE.Vector3(
      tunnel.endPoint.x * scale,
      tunnel.endPoint.y * scale,
      tunnel.endPoint.z * scale
    ),
  ], [tunnel, scale]);

  // Calculate midpoint for label
  const midpoint = useMemo(() => new THREE.Vector3(
    (tunnel.startPoint.x + tunnel.endPoint.x) / 2 * scale,
    (tunnel.startPoint.y + tunnel.endPoint.y) / 2 * scale + 2,
    (tunnel.startPoint.z + tunnel.endPoint.z) / 2 * scale
  ), [tunnel, scale]);

  // Create curve for tube
  const curve = useMemo(() => {
    return new THREE.LineCurve3(points[0], points[1]);
  }, [points]);

  return (
    <group>
      {/* Wireframe representation */}
      {showWireframe && (
        <>
          <CustomLine points={points} color={color} lineWidth={2} />
          {/* Glow effect for main tunnels */}
          {tunnel.type === 'main_tunnel' && (
            <CustomLine points={points} color={color} lineWidth={4} opacity={0.3} />
          )}
        </>
      )}

      {/* Solid tube representation */}
      {showSolid && (
        <Tube args={[curve, 20, tunnel.width * scale * 0.3, 8, false]}>
          <meshStandardMaterial
            color={color}
            transparent
            opacity={0.4}
            side={THREE.DoubleSide}
          />
        </Tube>
      )}

      {/* Label */}
      {showLabel && tunnel.type !== 'crosscut' && (
        <Text
          position={midpoint}
          fontSize={1.5}
          color={color}
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.1}
          outlineColor="#000000"
        >
          {tunnel.name}
        </Text>
      )}
    </group>
  );
};

// Station marker component
const StationMarker = ({ 
  station, 
  showLabel,
  scale = 1 
}: { 
  station: MineStation; 
  showLabel: boolean;
  scale?: number;
}) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const color = getStationColor(station.type);
  
  // Pulse animation for important stations
  useFrame((state) => {
    if (meshRef.current && (station.type === 'refuge' || station.type === 'emergency_exit')) {
      const pulse = Math.sin(state.clock.elapsedTime * 2) * 0.2 + 1;
      meshRef.current.scale.setScalar(pulse);
    }
  });

  const position: [number, number, number] = [
    station.position.x * scale,
    station.position.y * scale,
    station.position.z * scale,
  ];

  const size = station.type === 'loading' ? 2 : 
               station.type === 'refuge' ? 1.8 : 
               station.type === 'emergency_exit' ? 2 : 1.5;

  return (
    <group position={position}>
      {/* Station sphere */}
      <Sphere ref={meshRef} args={[size, 16, 16]}>
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.5}
          transparent
          opacity={0.8}
        />
      </Sphere>
      
      {/* Outer glow */}
      <Sphere args={[size * 1.5, 16, 16]}>
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.2}
        />
      </Sphere>

      {/* Label */}
      {showLabel && (
        <Text
          position={[0, size + 2, 0]}
          fontSize={1.2}
          color={color}
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.08}
          outlineColor="#000000"
        >
          {station.name}
        </Text>
      )}
    </group>
  );
};

// Shaft component (vertical connection)
const ShaftMesh = ({ 
  shaft, 
  showWireframe,
  showSolid,
  scale = 1 
}: { 
  shaft: ShaftData; 
  showWireframe: boolean;
  showSolid: boolean;
  scale?: number;
}) => {
  const color = shaft.type === 'main' ? MINE_COLORS.shaft : 
                shaft.type === 'ventilation' ? MINE_COLORS.ventilation :
                '#6366f1';

  const points = useMemo(() => [
    new THREE.Vector3(
      shaft.topPoint.x * scale,
      shaft.topPoint.y * scale,
      shaft.topPoint.z * scale
    ),
    new THREE.Vector3(
      shaft.bottomPoint.x * scale,
      shaft.bottomPoint.y * scale,
      shaft.bottomPoint.z * scale
    ),
  ], [shaft, scale]);

  const height = Math.abs(shaft.topPoint.y - shaft.bottomPoint.y) * scale;
  const midY = ((shaft.topPoint.y + shaft.bottomPoint.y) / 2) * scale;

  return (
    <group>
      {/* Wireframe vertical line */}
      {showWireframe && (
        <>
          <CustomLine points={points} color={color} lineWidth={2} />
          <CustomLine points={points} color={color} lineWidth={4} opacity={0.2} />
        </>
      )}

      {/* Solid cylinder */}
      {showSolid && (
        <mesh 
          position={[shaft.topPoint.x * scale, midY, shaft.topPoint.z * scale]}
          rotation={[0, 0, 0]}
        >
          <cylinderGeometry args={[shaft.diameter * scale * 0.5, shaft.diameter * scale * 0.5, height, 16]} />
          <meshStandardMaterial
            color={color}
            transparent
            opacity={0.3}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}

      {/* Top marker */}
      <Sphere 
        args={[shaft.diameter * scale * 0.3, 16, 16]} 
        position={[shaft.topPoint.x * scale, shaft.topPoint.y * scale, shaft.topPoint.z * scale]}
      >
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.3} />
      </Sphere>

      {/* Label at top */}
      <Text
        position={[shaft.topPoint.x * scale, shaft.topPoint.y * scale + 3, shaft.topPoint.z * scale]}
        fontSize={1.5}
        color={color}
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.1}
        outlineColor="#000000"
      >
        {shaft.name}
      </Text>
    </group>
  );
};

// Ramp component (spiral/decline path)
const RampMesh = ({ 
  ramp, 
  showWireframe,
  showSolid,
  scale = 1 
}: { 
  ramp: RampData; 
  showWireframe: boolean;
  showSolid: boolean;
  scale?: number;
}) => {
  const color = MINE_COLORS.ramp;

  const points = useMemo(() => 
    ramp.points.map(p => new THREE.Vector3(p.x * scale, p.y * scale, p.z * scale)),
  [ramp, scale]);

  const curve = useMemo(() => {
    return new THREE.CatmullRomCurve3(points);
  }, [points]);

  const curvePoints = useMemo(() => curve.getPoints(50), [curve]);

  return (
    <group>
      {/* Wireframe path */}
      {showWireframe && (
        <>
          <CustomLine points={curvePoints} color={color} lineWidth={2} />
          <CustomLine points={curvePoints} color={color} lineWidth={4} opacity={0.2} />
        </>
      )}

      {/* Solid tube */}
      {showSolid && (
        <Tube args={[curve, 64, ramp.width * scale * 0.3, 8, false]}>
          <meshStandardMaterial
            color={color}
            transparent
            opacity={0.35}
            side={THREE.DoubleSide}
          />
        </Tube>
      )}

      {/* Label at top */}
      <Text
        position={[ramp.points[0].x * scale, ramp.points[0].y * scale + 3, ramp.points[0].z * scale]}
        fontSize={1.5}
        color={color}
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.1}
        outlineColor="#000000"
      >
        {ramp.name}
      </Text>
    </group>
  );
};

// Main TunnelNetwork component
const TunnelNetwork = ({
  tunnels,
  stations,
  shafts,
  ramps,
  showWireframe,
  showSolidTunnels,
  showLabels,
  selectedLevel,
  scale = 0.1,
}: TunnelNetworkProps) => {
  // Filter tunnels by selected level if specified
  const filteredTunnels = useMemo(() => {
    if (selectedLevel === null) return tunnels;
    return tunnels.filter(t => t.level === selectedLevel);
  }, [tunnels, selectedLevel]);

  // Filter stations by level
  const filteredStations = useMemo(() => {
    if (selectedLevel === null) return stations;
    const targetDepth = selectedLevel * -50; // Convert level to depth
    return stations.filter(s => Math.abs(s.position.y - targetDepth) < 25);
  }, [stations, selectedLevel]);

  return (
    <group>
      {/* Render all tunnels */}
      {filteredTunnels.map(tunnel => (
        <TunnelSegmentMesh
          key={tunnel.id}
          tunnel={tunnel}
          showWireframe={showWireframe}
          showSolid={showSolidTunnels}
          showLabel={showLabels}
          scale={scale}
        />
      ))}

      {/* Render all stations */}
      {filteredStations.map(station => (
        <StationMarker
          key={station.id}
          station={station}
          showLabel={showLabels}
          scale={scale}
        />
      ))}

      {/* Render shafts (always visible) */}
      {shafts.map(shaft => (
        <ShaftMesh
          key={shaft.id}
          shaft={shaft}
          showWireframe={showWireframe}
          showSolid={showSolidTunnels}
          scale={scale}
        />
      ))}

      {/* Render ramps (always visible) */}
      {ramps.map(ramp => (
        <RampMesh
          key={ramp.id}
          ramp={ramp}
          showWireframe={showWireframe}
          showSolid={showSolidTunnels}
          scale={scale}
        />
      ))}
    </group>
  );
};

export default TunnelNetwork;
