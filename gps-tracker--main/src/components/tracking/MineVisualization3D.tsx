import { useRef, useMemo, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Line, Text, Html, Billboard } from '@react-three/drei';
import * as THREE from 'three';
import { mineLayout } from '@/data/mineLayout3D';
import { GPSPosition, Device } from '@/types/tracking';

// Constants for coordinate conversion
const METERS_PER_DEG_LAT = 111320;
const METERS_PER_DEG_LNG = 103000;

interface MineVisualization3DProps {
  currentPosition: GPSPosition | null;
  trackHistory: GPSPosition[];
  device: Device | null;
  devices?: Device[];
  allDevicePositions?: Map<string, GPSPosition>;
  allDeviceTrackHistory?: Map<string, GPSPosition[]>;
  isUnderground?: boolean;
  showWireframe?: boolean;
  showLevels?: boolean;
  playbackIndex?: number;
}

// Animated beacon for stations
const StationBeacon = ({ position, color, label, type, pulse = true }: { 
  position: [number, number, number]; 
  color: string; 
  label?: string;
  type: string;
  pulse?: boolean;
}) => {
  const ref = useRef<THREE.Group>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (ringRef.current && pulse) {
      const scale = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.3;
      ringRef.current.scale.set(scale, scale, 1);
      const material = ringRef.current.material as THREE.Material;
      if ('opacity' in material) {
        material.opacity = 0.4 - Math.sin(state.clock.elapsedTime * 2) * 0.2;
      }
    }
  });

  const size = type === 'shaft_entry' ? 4 : type === 'junction' ? 2 : 3;
  const icon = type === 'shaft_entry' ? '⬆' : type === 'end' ? '◉' : '◎';

  return (
    <group ref={ref} position={position}>
      {/* Core sphere */}
      <mesh>
        <sphereGeometry args={[size, 16, 16]} />
        <meshStandardMaterial 
          color={color} 
          emissive={color} 
          emissiveIntensity={0.8}
          transparent 
          opacity={0.9}
        />
      </mesh>
      
      {/* Outer glow ring */}
      <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[size * 1.5, size * 2, 32]} />
        <meshBasicMaterial color={color} transparent opacity={0.3} side={THREE.DoubleSide} />
      </mesh>
      
      {/* Vertical beam (for main stations) */}
      {(type === 'shaft_entry' || type === 'junction') && (
        <mesh position={[0, 15, 0]}>
          <cylinderGeometry args={[0.3, 0.3, 30, 8]} />
          <meshBasicMaterial color={color} transparent opacity={0.15} />
        </mesh>
      )}
      
      {/* Label */}
      {label && (
        <Billboard position={[0, size + 8, 0]}>
          <Html center>
            <div className="flex flex-col items-center gap-1 pointer-events-none">
              <div className="text-lg">{icon}</div>
              <div 
                className="px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap backdrop-blur-md border shadow-lg"
                style={{ 
                  backgroundColor: `${color}20`,
                  borderColor: `${color}60`,
                  color: color,
                  textShadow: `0 0 10px ${color}`
                }}
              >
                {label}
              </div>
            </div>
          </Html>
        </Billboard>
      )}
    </group>
  );
};

// Animated tunnel wireframe
const TunnelWireframe = ({ start, end, color, width, type }: {
  start: [number, number, number];
  end: [number, number, number];
  color: string;
  width: number;
  type: string;
}) => {
  const ref = useRef<THREE.Group>(null);
  
  // Create tube-like wireframe effect
  const midPoint: [number, number, number] = [
    (start[0] + end[0]) / 2,
    (start[1] + end[1]) / 2,
    (start[2] + end[2]) / 2
  ];

  const isMainShaft = type === 'main_shaft';
  const isRamp = type === 'ramp';

  return (
    <group ref={ref}>
      {/* Main line - bright and visible */}
      <Line
        points={[start, end]}
        color={color}
        lineWidth={isMainShaft ? 6 : isRamp ? 4 : 3}
      />
      
      {/* Glow effect - second line behind */}
      <Line
        points={[start, end]}
        color={color}
        lineWidth={isMainShaft ? 12 : isRamp ? 8 : 6}
        transparent
        opacity={0.3}
      />
      
      {/* Parallel lines for tunnel walls */}
      <Line
        points={[
          [start[0] + width/2, start[1], start[2]],
          [end[0] + width/2, end[1], end[2]]
        ]}
        color={color}
        lineWidth={1}
        transparent
        opacity={0.5}
      />
      <Line
        points={[
          [start[0] - width/2, start[1], start[2]],
          [end[0] - width/2, end[1], end[2]]
        ]}
        color={color}
        lineWidth={1}
        transparent
        opacity={0.5}
      />
      
      {/* Cross supports for main shaft */}
      {isMainShaft && (
        <>
          <Line
            points={[
              [start[0] - width, start[1], start[2]],
              [start[0] + width, start[1], start[2]]
            ]}
            color={color}
            lineWidth={3}
            transparent
            opacity={0.7}
          />
          <Line
            points={[
              [end[0] - width, end[1], end[2]],
              [end[0] + width, end[1], end[2]]
            ]}
            color={color}
            lineWidth={3}
            transparent
            opacity={0.7}
          />
        </>
      )}
    </group>
  );
};

// Simba Drill - Distinctive orange/yellow drill with rotating bit
const SimbaDrill = ({ 
  position, 
  heading, 
  device,
  health 
}: { 
  position: [number, number, number]; 
  heading: number; 
  device: Device | null;
  health: {
    battery: number;
    signal: number;
    status: string;
  };
}) => {
  const ref = useRef<THREE.Group>(null);
  const drillBitRef = useRef<THREE.Group>(null);
  const beaconRef = useRef<THREE.PointLight>(null);
  const glow1Ref = useRef<THREE.Mesh>(null);
  const glow2Ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (ref.current) {
      ref.current.position.set(position[0], position[1], position[2]);
      ref.current.rotation.y = -heading * (Math.PI / 180);
    }

    // Rotate drill bit
    if (drillBitRef.current) {
      drillBitRef.current.rotation.z += 0.3; // Continuous rotation
    }

    // Animate beacon pulse
    if (beaconRef.current && glow1Ref.current && glow2Ref.current) {
      const pulse = Math.sin(state.clock.elapsedTime * 4) * 0.5 + 1.5;
      beaconRef.current.intensity = pulse * 2;
      glow1Ref.current.scale.setScalar(pulse * 1.2);
      glow2Ref.current.scale.setScalar(pulse * 1.5);
    }
  });

  const statusColor = health.status === 'emergency' ? '#ef4444' : 
                      health.status === 'breakdown' ? '#f59e0b' : '#f97316';
  const simbaColor = '#f97316'; // Orange color for Simba

  return (
    <group ref={ref} position={position}>
      {/* Main Drill Body - Large rectangular chassis */}
      <mesh position={[0, 2, 0]}>
        <boxGeometry args={[8, 5, 12]} />
        <meshStandardMaterial color={simbaColor} emissive={simbaColor} emissiveIntensity={0.3} wireframe />
      </mesh>

      {/* Drill Arm - Extends forward */}
      <group ref={drillBitRef} position={[0, 2, -8]}>
        {/* Drill Shaft */}
        <mesh rotation-x={Math.PI / 2}>
          <cylinderGeometry args={[0.8, 0.8, 10, 16]} />
          <meshStandardMaterial color="#64748b" wireframe />
        </mesh>
        
        {/* Rotating Drill Bit */}
        <mesh position={[0, 0, -5]}>
          <coneGeometry args={[1.5, 3, 12]} />
          <meshStandardMaterial color={statusColor} emissive={statusColor} emissiveIntensity={0.6} />
        </mesh>
        
        {/* Drill Bit Rotation Indicator Rings */}
        <mesh position={[0, 0, -3]} rotation-x={Math.PI / 2}>
          <torusGeometry args={[1.2, 0.1, 8, 16]} />
          <meshStandardMaterial color={simbaColor} emissive={simbaColor} />
        </mesh>
        <mesh position={[0, 0, -4]} rotation-x={Math.PI / 2}>
          <torusGeometry args={[1.2, 0.1, 8, 16]} />
          <meshStandardMaterial color={simbaColor} emissive={simbaColor} />
        </mesh>
      </group>

      {/* Large Orange Beacon */}
      <group position={[0, 6, 0]}>
        <pointLight ref={beaconRef} color={simbaColor} distance={50} decay={2} />
        <mesh>
          <sphereGeometry args={[6, 16, 16]} />
          <meshBasicMaterial color={simbaColor} transparent opacity={0.5} />
        </mesh>
        {/* Pulsing Glow Halos */}
        <mesh ref={glow1Ref}>
          <sphereGeometry args={[9, 16, 16]} />
          <meshBasicMaterial color={simbaColor} transparent opacity={0.15} />
        </mesh>
        <mesh ref={glow2Ref}>
          <sphereGeometry args={[13, 16, 16]} />
          <meshBasicMaterial color={simbaColor} transparent opacity={0.08} />
        </mesh>
        {/* Vertical Beam */}
        <mesh position={[0, 12, 0]}>
          <cylinderGeometry args={[0.5, 0.5, 24, 8]} />
          <meshBasicMaterial color={simbaColor} transparent opacity={0.2} />
        </mesh>
      </group>

      {/* Direction Arrow - Orange */}
      <mesh position={[0, 3, -6]} rotation-x={Math.PI / 2}>
        <coneGeometry args={[1.2, 4, 8]} />
        <meshStandardMaterial color={simbaColor} emissive={simbaColor} emissiveIntensity={0.8} />
      </mesh>

      {/* Health HUD */}
      <Html position={[0, 10, 0]} center distanceFactor={50}>
        <div className="bg-gradient-to-br from-gray-900/90 to-black/90 text-white px-4 py-3 rounded-lg border border-orange-500 shadow-lg min-w-[200px] font-mono relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-full bg-orange-500 opacity-10 animate-pulse-slow pointer-events-none"></div>
          <div className="flex items-center justify-between text-sm mb-2 border-b border-gray-700 pb-2">
            <span className="font-bold text-lg text-orange-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-orange-500 animate-ping-slow" />
              {device?.name || 'SIMBA DRILL'}
            </span>
            <span className="text-xs text-gray-400">ACTIVE</span>
          </div>
          <div className="space-y-1 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">STATUS:</span>
              <span className={`font-semibold ${
                health.status === 'emergency' ? 'text-red-400' : 
                health.status === 'breakdown' ? 'text-yellow-400' : 'text-green-400'
              }`}>
                {health.status?.toUpperCase() || 'OPERATIONAL'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">BATTERY:</span>
              <span className={`font-semibold ${
                health.battery > 60 ? 'text-green-400' : 
                health.battery > 20 ? 'text-yellow-400' : 'text-red-400'
              }`}>{health.battery}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">SIGNAL:</span>
              <span className={`font-semibold ${
                health.signal > 75 ? 'text-green-400' : 
                health.signal > 40 ? 'text-yellow-400' : 'text-red-400'
              }`}>{health.signal}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">DEPTH:</span>
              <span className="font-semibold text-blue-400">{position[1] ? (-position[1]).toFixed(1) : 0}m</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">HEADING:</span>
              <span className="font-semibold text-purple-400">{heading.toFixed(0)}°</span>
            </div>
          </div>
        </div>
      </Html>
    </group>
  );
};

// Vehicle - Large Teal Sphere (Mobilaris Style)
const Vehicle = ({ 
  position, 
  heading, 
  device,
  health 
}: { 
  position: [number, number, number]; 
  heading: number; 
  device: Device | null;
  health: {
    battery: number;
    signal: number;
    status: string;
  };
}) => {
  const ref = useRef<THREE.Group>(null);
  const sphereRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (ref.current) {
      ref.current.position.lerp(new THREE.Vector3(...position), 0.1);
    }
    
    // Subtle pulse effect
    if (sphereRef.current) {
      const pulse = Math.sin(state.clock.elapsedTime * 2) * 0.1 + 1;
      sphereRef.current.scale.setScalar(pulse);
    }
  });

  // Teal/Cyan color for the sphere
  const sphereColor = '#22d3ee';

  return (
    <group ref={ref} position={position}>
      {/* Main glowing sphere - LARGE AND VISIBLE */}
      <pointLight position={[0, 0, 0]} intensity={20} distance={100} color={sphereColor} />
      
      {/* Core sphere */}
      <mesh ref={sphereRef}>
        <sphereGeometry args={[12, 32, 32]} />
        <meshStandardMaterial 
          color={sphereColor} 
          emissive={sphereColor}
          emissiveIntensity={0.5}
          transparent
          opacity={0.9}
        />
      </mesh>
      
      {/* Outer glow */}
      <mesh>
        <sphereGeometry args={[15, 32, 32]} />
        <meshBasicMaterial color={sphereColor} transparent opacity={0.2} />
      </mesh>
      
      {/* Direction indicator line */}
      <Line
        points={[
          [0, 0, 0],
          [0, 0, 25]
        ]}
        color={sphereColor}
        lineWidth={3}
      />
      
      {/* Trail showing path */}
      <Line
        points={[
          [0, 0, -40],
          [0, 0, -30],
          [0, 0, -20],
          [0, 0, -10],
          [0, 0, 0]
        ]}
        color={sphereColor}
        lineWidth={2}
        transparent
        opacity={0.4}
      />
    </group>
  );
};

// Enhanced tunnel system
const Tunnels = () => {
  const tunnelGeometries = useMemo(() => {
    return mineLayout.tunnels.map(tunnel => {
      const startNode = mineLayout.nodes.find(n => n.id === tunnel.startNodeId);
      const endNode = mineLayout.nodes.find(n => n.id === tunnel.endNodeId);
      
      if (!startNode || !endNode) return null;

      const start: [number, number, number] = [
        startNode.position.x, 
        startNode.position.y, 
        startNode.position.z
      ];
      const end: [number, number, number] = [
        endNode.position.x, 
        endNode.position.y, 
        endNode.position.z
      ];

      // Color based on depth and type
      let color = '#3b82f6'; // Default blue
      const avgDepth = (startNode.position.y + endNode.position.y) / 2;
      
      if (tunnel.type === 'main_shaft') {
        color = '#a855f7'; // Purple for main shaft
      } else if (tunnel.type === 'ramp') {
        color = '#06b6d4'; // Cyan for ramps
      } else if (avgDepth <= -200) {
        color = '#ef4444'; // Red for deep
      } else if (avgDepth <= -100) {
        color = '#f59e0b'; // Orange for mid
      } else {
        color = '#0eb8c3'; // Teal for shallow
      }

      return (
        <TunnelWireframe
          key={tunnel.id}
          start={start}
          end={end}
          color={color}
          width={tunnel.width || 4}
          type={tunnel.type}
        />
      );
    });
  }, []);

  return <group>{tunnelGeometries}</group>;
};

// Station nodes
const Stations = () => {
  return (
    <group>
      {mineLayout.nodes.map(node => {
        // Color based on depth
        let color = '#0eb8c3';
        if (node.position.y <= -200) color = '#ef4444';
        else if (node.position.y <= -100) color = '#f59e0b';
        else if (node.type === 'shaft_entry') color = '#22c55e';
        
        return (
          <StationBeacon
            key={node.id}
            position={[node.position.x, node.position.y, node.position.z]}
            color={color}
            label={node.label}
            type={node.type}
            pulse={node.type !== 'junction' || !!node.label}
          />
        );
      })}
    </group>
  );
};

// Enhanced grid with depth indicators
const DepthGrid = () => {
  return (
    <group>
      {/* Surface ground plane */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]}>
        <planeGeometry args={[800, 800]} />
        <meshStandardMaterial color="#0c1222" transparent opacity={0.8} />
      </mesh>
      
      {/* Surface grid - brighter */}
      <gridHelper args={[800, 20, '#2563eb', '#1e3a5f']} position={[0, 0, 0]} />
      
      {/* Level grids with glow effect */}
      {mineLayout.levels.map(level => (
        <group key={level.id} position={[0, level.depth, 0]}>
          {/* Level floor */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]}>
            <planeGeometry args={[400, 400]} />
            <meshStandardMaterial color={level.color} transparent opacity={0.05} />
          </mesh>
          
          <gridHelper 
            args={[400, 10, level.color, '#1e293b']} 
            position={[0, 0, 0]} 
          />
          
          {/* Level boundary ring */}
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <ringGeometry args={[195, 200, 64]} />
            <meshBasicMaterial color={level.color} transparent opacity={0.25} side={THREE.DoubleSide} />
          </mesh>
          
          {/* Level label */}
          <Billboard position={[220, 0, 0]}>
            <Html center>
              <div 
                className="px-4 py-2 rounded-lg font-bold text-sm whitespace-nowrap backdrop-blur-sm border"
                style={{ 
                  backgroundColor: `${level.color}15`,
                  borderColor: `${level.color}40`,
                  color: level.color
                }}
              >
                {level.name}
                <div className="text-xs opacity-70 font-mono">{level.depth}m</div>
              </div>
            </Html>
          </Billboard>
        </group>
      ))}
      
      {/* Depth scale */}
      <group position={[-250, 0, 0]}>
        {[0, -50, -100, -150, -200, -250, -300].map(depth => (
          <group key={depth} position={[0, depth, 0]}>
            <Line
              points={[[-10, 0, 0], [10, 0, 0]]}
              color="#64748b"
              lineWidth={2}
            />
            <Text
              position={[-25, 0, 0]}
              color="#94a3b8"
              fontSize={10}
              anchorX="right"
            >
              {depth}m
            </Text>
          </group>
        ))}
        {/* Vertical scale line */}
        <Line
          points={[[0, 0, 0], [0, -300, 0]]}
          color="#475569"
          lineWidth={2}
        />
      </group>
      
      {/* Central vertical shaft indicator */}
      <mesh position={[0, -150, 0]}>
        <cylinderGeometry args={[8, 8, 300, 16, 1, true]} />
        <meshBasicMaterial color="#a855f7" transparent opacity={0.1} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
};

// Track history trail
const TrackTrail = ({ positions, centerRef, color = "#0eb8c3" }: { 
  positions: GPSPosition[]; 
  centerRef: { lat: number; lng: number };
  color?: string;
}) => {
  const points = useMemo(() => {
    return positions.slice(-100).map(pos => {
      const dLat = pos.latitude - centerRef.lat;
      const dLng = pos.longitude - centerRef.lng;
      return [
        dLng * METERS_PER_DEG_LNG,
        -(pos.depth || 0),
        -dLat * METERS_PER_DEG_LAT
      ] as [number, number, number];
    });
  }, [positions, centerRef]);

  if (points.length < 2) return null;

  return (
    <Line
      points={points}
      color={color}
      lineWidth={3}
      transparent
      opacity={0.6}
    />
  );
};

const MineVisualization3D = ({ 
  currentPosition, 
  trackHistory,
  device, 
  devices = [],
  allDevicePositions = new Map(),
  allDeviceTrackHistory = new Map(),
  isUnderground,
  showWireframe = true,
  showLevels = true,
  playbackIndex = -1
}: MineVisualization3DProps) => {
  // Get position from playback or current position
  const activePosition = useMemo(() => {
    if (playbackIndex >= 0 && playbackIndex < trackHistory.length) {
      return trackHistory[playbackIndex];
    }
    return currentPosition;
  }, [playbackIndex, trackHistory, currentPosition]);

  const vehiclePosition = useMemo(() => {
    if (!activePosition) return [0, 0, 0] as [number, number, number];

    const dLat = activePosition.latitude - mineLayout.centerReference.lat;
    const dLng = activePosition.longitude - mineLayout.centerReference.lng;

    const x = dLng * METERS_PER_DEG_LNG;
    const z = -dLat * METERS_PER_DEG_LAT;
    const y = -(activePosition.depth || 0);

    return [x, y, z] as [number, number, number];
  }, [activePosition]);

  const vehicleHealth = useMemo(() => ({
    battery: activePosition?.battery || 85,
    signal: activePosition?.signalStrength || 100,
    status: device?.status || 'operational'
  }), [activePosition, device]);

  const vehicleHeading = activePosition?.heading || 0;
  
  // Check if device is Simba drill (by name)
  const isSimbaDrill = device?.name?.toLowerCase().includes('simba') || false;

  return (
    <div className="w-full h-full bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 rounded-xl overflow-hidden relative">
      {/* HUD Overlay */}
      <div className="absolute top-4 left-4 z-10 pointer-events-none space-y-2">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isUnderground ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`} />
          <span className="text-white/80 font-mono text-sm bg-black/50 px-3 py-1.5 rounded-lg backdrop-blur-sm border border-white/10">
            {isUnderground ? '⛏️ UNDERGROUND MODE' : '☀️ SURFACE MODE'}
          </span>
        </div>
        
        {currentPosition && (
          <div className="bg-black/50 px-3 py-2 rounded-lg backdrop-blur-sm border border-white/10 text-xs font-mono text-slate-400 space-y-1">
            <div>LAT: <span className="text-white">{currentPosition.latitude.toFixed(6)}°</span></div>
            <div>LNG: <span className="text-white">{currentPosition.longitude.toFixed(6)}°</span></div>
            <div>DEPTH: <span className="text-cyan-400">{(currentPosition.depth || 0).toFixed(1)}m</span></div>
            <div>SPEED: <span className="text-white">{(currentPosition.speed || 0).toFixed(1)} km/h</span></div>
          </div>
        )}
      </div>
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 pointer-events-none">
        <div className="bg-black/50 px-3 py-2 rounded-lg backdrop-blur-sm border border-white/10 text-[10px] font-mono space-y-1">
          <div className="text-slate-500 uppercase tracking-wider mb-2">Mine Levels</div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-cyan-500 rounded" />
            <span className="text-cyan-400">Level 1 (-50m)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-amber-500 rounded" />
            <span className="text-amber-400">Level 2 (-150m)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-red-500 rounded" />
            <span className="text-red-400">Level 3 (-250m)</span>
          </div>
          <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-700">
            <div className="w-3 h-0.5 bg-purple-500 rounded" />
            <span className="text-purple-400">Main Shaft</span>
          </div>
        </div>
      </div>

      {/* Controls hint */}
      <div className="absolute bottom-4 right-4 z-10 pointer-events-none">
        <div className="bg-black/50 px-3 py-2 rounded-lg backdrop-blur-sm border border-white/10 text-[10px] font-mono text-slate-500">
          <div>🖱️ Left drag: Rotate</div>
          <div>🖱️ Right drag: Pan</div>
          <div>🖱️ Scroll: Zoom</div>
        </div>
      </div>
      
      <Canvas camera={{ position: [300, 150, 300], fov: 60 }}>
        <color attach="background" args={['#0a0f1a']} />
        
        {/* Ambient lighting - brighter */}
        <ambientLight intensity={0.6} />
        <directionalLight position={[200, 200, 100]} intensity={0.8} color="#ffffff" />
        <directionalLight position={[-100, 100, -100]} intensity={0.3} color="#0ea5e9" />
        
        {/* Dynamic vehicle light */}
        {currentPosition && (
          <pointLight 
            position={vehiclePosition} 
            intensity={8} 
            distance={100} 
            color="#0eb8c3" 
          />
        )}
        
        {/* Global scene lighting */}
        <pointLight position={[0, -50, 0]} intensity={3} distance={200} color="#0eb8c3" />
        <pointLight position={[0, -150, 0]} intensity={3} distance={200} color="#f59e0b" />
        <pointLight position={[0, -250, 0]} intensity={3} distance={200} color="#ef4444" />
        
        <OrbitControls 
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          minDistance={50}
          maxDistance={1000}
          target={[0, -100, 0]}
          maxPolarAngle={Math.PI * 0.85}
        />
        
        {showLevels && <DepthGrid />}
        {showWireframe && <Tunnels />}
        <Stations />
        
        {/* Track trails for all devices */}
        {Array.from(allDeviceTrackHistory.entries()).map(([deviceId, positions], index) => {
          const deviceInfo = devices.find(d => d.id === deviceId);
          if (!deviceInfo || positions.length < 2) return null;
          
          // Different colors for different devices - bright, visible colors
          const colors = ['#0eb8c3', '#f97316', '#22c55e', '#a855f7', '#f59e0b', '#ef4444'];
          const trailColor = colors[index % colors.length];
          
          return (
            <TrackTrail 
              key={`trail-${deviceId}`}
              positions={positions} 
              centerRef={mineLayout.centerReference}
              color={trailColor}
            />
          );
        })}
        
        {/* Current device trail if not in allDeviceTrackHistory */}
        {trackHistory.length >= 2 && (
          <TrackTrail 
            positions={trackHistory} 
            centerRef={mineLayout.centerReference}
            color="#0eb8c3"
          />
        )}
        
        {/* Render all devices */}
        {Array.from(allDevicePositions.entries()).map(([deviceId, position]) => {
          const deviceInfo = devices.find(d => d.id === deviceId) || device;
          if (!deviceInfo || !position) return null;
          
          // Convert position to 3D coordinates
          const dLat = position.latitude - mineLayout.centerReference.lat;
          const dLng = position.longitude - mineLayout.centerReference.lng;
          const x = dLng * METERS_PER_DEG_LNG;
          const z = -dLat * METERS_PER_DEG_LAT;
          const y = -(position.depth || 0);
          const pos: [number, number, number] = [x, y, z];
          
          const health = {
            battery: position.battery || 85,
            signal: position.signalStrength || 100,
            status: deviceInfo.status || 'operational'
          };
          
          const isSimba = deviceInfo.name?.toLowerCase().includes('simba') || false;
          
          return isSimba ? (
            <SimbaDrill 
              key={deviceId}
              position={pos} 
              heading={position.heading || 0}
              device={deviceInfo}
              health={health}
            />
          ) : (
            <Vehicle 
              key={deviceId}
              position={pos} 
              heading={position.heading || 0}
              device={deviceInfo}
              health={health}
            />
          );
        })}
        
        {/* Also render current device if it's not in allDevicePositions */}
        {activePosition && !allDevicePositions.has(device?.id || '') && (
          isSimbaDrill ? (
            <SimbaDrill 
              position={vehiclePosition} 
              heading={vehicleHeading}
              device={device}
              health={vehicleHealth}
            />
          ) : (
            <Vehicle 
              position={vehiclePosition} 
              heading={vehicleHeading}
              device={device}
              health={vehicleHealth}
            />
          )
        )}
        
        {/* Subtle fog for depth - moved much further */}
        <fog attach="fog" args={['#0a0f1a', 500, 1200]} />
      </Canvas>
    </div>
  );
};

export default MineVisualization3D;
