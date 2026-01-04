// Vehicle3D.tsx - Renders the mining vehicle in 3D space
import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Billboard, Sphere } from '@react-three/drei';
import * as THREE from 'three';
import { MINE_COLORS, Point3D } from '@/types/mine3d';

interface Vehicle3DProps {
  position: Point3D;
  heading: number;
  speed: number;
  name: string;
  status: 'moving' | 'stopped' | 'loading' | 'emergency' | 'breakdown';
  scale?: number;
  showTrail?: boolean;
  trailPositions?: Point3D[];
}

// Get color based on vehicle status
const getVehicleColor = (status: Vehicle3DProps['status']): string => {
  switch (status) {
    case 'moving':
    case 'stopped':
    case 'loading':
      return MINE_COLORS.vehicleActive;
    case 'emergency':
      return MINE_COLORS.vehicleEmergency;
    case 'breakdown':
      return MINE_COLORS.vehicleBreakdown;
    default:
      return MINE_COLORS.vehicleActive;
  }
};

// Mining truck 3D model (simplified geometric representation)
const MiningTruckModel = ({ 
  color, 
  status 
}: { 
  color: string; 
  status: Vehicle3DProps['status'];
}) => {
  const bodyRef = useRef<THREE.Group>(null);
  const wheelRefs = useRef<THREE.Mesh[]>([]);

  // Animation for emergency/breakdown
  useFrame((state) => {
    if (bodyRef.current) {
      if (status === 'emergency' || status === 'breakdown') {
        // Pulsing effect
        const pulse = Math.sin(state.clock.elapsedTime * 5) * 0.1 + 1;
        bodyRef.current.scale.setScalar(pulse);
      }
      
      // Rotate wheels if moving
      if (status === 'moving') {
        wheelRefs.current.forEach(wheel => {
          if (wheel) {
            wheel.rotation.x += 0.1;
          }
        });
      }
    }
  });

  return (
    <group ref={bodyRef}>
      {/* Main body (cab) */}
      <mesh position={[0, 1.5, 0.5]}>
        <boxGeometry args={[2, 1.5, 2]} />
        <meshStandardMaterial 
          color={color} 
          emissive={color}
          emissiveIntensity={status === 'emergency' ? 0.8 : 0.3}
        />
      </mesh>

      {/* Cargo bed */}
      <mesh position={[0, 1, -1.5]}>
        <boxGeometry args={[2.2, 1, 3]} />
        <meshStandardMaterial 
          color={color} 
          emissive={color}
          emissiveIntensity={0.2}
        />
      </mesh>

      {/* Front wheels */}
      <mesh 
        position={[1, 0.4, 1]} 
        rotation={[0, 0, Math.PI / 2]}
        ref={(el) => { if (el) wheelRefs.current[0] = el; }}
      >
        <cylinderGeometry args={[0.4, 0.4, 0.3, 16]} />
        <meshStandardMaterial color="#1f2937" />
      </mesh>
      <mesh 
        position={[-1, 0.4, 1]} 
        rotation={[0, 0, Math.PI / 2]}
        ref={(el) => { if (el) wheelRefs.current[1] = el; }}
      >
        <cylinderGeometry args={[0.4, 0.4, 0.3, 16]} />
        <meshStandardMaterial color="#1f2937" />
      </mesh>

      {/* Rear wheels (larger) */}
      <mesh 
        position={[1, 0.5, -2]} 
        rotation={[0, 0, Math.PI / 2]}
        ref={(el) => { if (el) wheelRefs.current[2] = el; }}
      >
        <cylinderGeometry args={[0.5, 0.5, 0.4, 16]} />
        <meshStandardMaterial color="#1f2937" />
      </mesh>
      <mesh 
        position={[-1, 0.5, -2]} 
        rotation={[0, 0, Math.PI / 2]}
        ref={(el) => { if (el) wheelRefs.current[3] = el; }}
      >
        <cylinderGeometry args={[0.5, 0.5, 0.4, 16]} />
        <meshStandardMaterial color="#1f2937" />
      </mesh>

      {/* Headlights */}
      <mesh position={[0.6, 1.3, 1.5]}>
        <sphereGeometry args={[0.15, 8, 8]} />
        <meshStandardMaterial 
          color="#ffffff" 
          emissive="#ffff00"
          emissiveIntensity={1}
        />
      </mesh>
      <mesh position={[-0.6, 1.3, 1.5]}>
        <sphereGeometry args={[0.15, 8, 8]} />
        <meshStandardMaterial 
          color="#ffffff" 
          emissive="#ffff00"
          emissiveIntensity={1}
        />
      </mesh>

      {/* Warning light on top (for emergency) */}
      {(status === 'emergency' || status === 'breakdown') && (
        <mesh position={[0, 2.5, 0.5]}>
          <sphereGeometry args={[0.3, 16, 16]} />
          <meshStandardMaterial 
            color={status === 'emergency' ? '#ef4444' : '#f59e0b'} 
            emissive={status === 'emergency' ? '#ef4444' : '#f59e0b'}
            emissiveIntensity={2}
          />
        </mesh>
      )}
    </group>
  );
};

// Vehicle trail (path history)
const VehicleTrail = ({ 
  positions, 
  color,
  scale 
}: { 
  positions: Point3D[]; 
  color: string;
  scale: number;
}) => {
  const points = useMemo(() => 
    positions.map(p => new THREE.Vector3(p.x * scale, p.y * scale, p.z * scale)),
  [positions, scale]);

  const geometry = useMemo(() => {
    if (points.length < 2) return null;
    return new THREE.BufferGeometry().setFromPoints(points);
  }, [points]);

  if (!geometry || points.length < 2) return null;

  return (
    <group>
      {/* Main trail line */}
      <line geometry={geometry}>
        <lineBasicMaterial color={color} transparent opacity={0.6} />
      </line>

      {/* Trail dots */}
      {positions.slice(-20).map((pos, i) => (
        <Sphere
          key={i}
          args={[0.1, 8, 8]}
          position={[pos.x * scale, pos.y * scale, pos.z * scale]}
        >
          <meshBasicMaterial 
            color={color} 
            transparent 
            opacity={0.3 + (i / 20) * 0.5} 
          />
        </Sphere>
      ))}
    </group>
  );
};

// Main Vehicle3D component
const Vehicle3D = ({
  position,
  heading,
  speed,
  name,
  status,
  scale = 0.1,
  showTrail = true,
  trailPositions = [],
}: Vehicle3DProps) => {
  const groupRef = useRef<THREE.Group>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const color = getVehicleColor(status);

  // Glow animation
  useFrame((state) => {
    if (glowRef.current) {
      const pulse = Math.sin(state.clock.elapsedTime * 3) * 0.3 + 0.7;
      glowRef.current.scale.setScalar(pulse * 8);
    }
  });

  // Convert position to 3D coordinates
  const pos3D: [number, number, number] = [
    position.x * scale,
    position.y * scale,
    position.z * scale,
  ];

  // Convert heading to radians (Y-axis rotation)
  const rotation: [number, number, number] = [0, -heading * (Math.PI / 180) + Math.PI / 2, 0];

  // Vertical line points
  const verticalLinePoints = useMemo(() => [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, -position.y * scale * 10, 0),
  ], [position.y, scale]);

  const verticalLineGeometry = useMemo(() => {
    return new THREE.BufferGeometry().setFromPoints(verticalLinePoints);
  }, [verticalLinePoints]);

  return (
    <group ref={groupRef}>
      {/* Trail */}
      {showTrail && trailPositions.length > 1 && (
        <VehicleTrail 
          positions={trailPositions} 
          color={color}
          scale={scale}
        />
      )}

      {/* Vehicle group */}
      <group position={pos3D} rotation={rotation}>
        {/* Ground glow effect */}
        <Sphere ref={glowRef} args={[1, 16, 16]} position={[0, 0.1, 0]}>
          <meshBasicMaterial 
            color={color} 
            transparent 
            opacity={0.15} 
          />
        </Sphere>

        {/* Mining truck model */}
        <MiningTruckModel color={color} status={status} />

        {/* Vertical position indicator line */}
        <line geometry={verticalLineGeometry}>
          <lineBasicMaterial color={color} transparent opacity={0.3} />
        </line>
      </group>

      {/* Billboard label (always faces camera) */}
      <Billboard position={[pos3D[0], pos3D[1] + 5, pos3D[2]]}>
        <group>
          {/* Background */}
          <mesh>
            <planeGeometry args={[12, 4]} />
            <meshBasicMaterial color="#000000" transparent opacity={0.7} />
          </mesh>
          
          {/* Name */}
          <Text
            position={[0, 0.8, 0.1]}
            fontSize={1}
            color={color}
            anchorX="center"
            anchorY="middle"
          >
            {name}
          </Text>

          {/* Status and speed */}
          <Text
            position={[0, -0.5, 0.1]}
            fontSize={0.7}
            color="#94a3b8"
            anchorX="center"
            anchorY="middle"
          >
            {status.toUpperCase()} | {speed.toFixed(1)} km/h
          </Text>

          {/* Depth indicator */}
          <Text
            position={[0, -1.3, 0.1]}
            fontSize={0.6}
            color="#64748b"
            anchorX="center"
            anchorY="middle"
          >
            Depth: {Math.abs(position.y).toFixed(0)}m
          </Text>
        </group>
      </Billboard>

      {/* Status indicator ring */}
      <mesh position={pos3D} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[3, 3.5, 32]} />
        <meshBasicMaterial 
          color={color} 
          transparent 
          opacity={status === 'emergency' || status === 'breakdown' ? 0.8 : 0.4}
          side={THREE.DoubleSide}
        />
      </mesh>
    </group>
  );
};

export default Vehicle3D;
