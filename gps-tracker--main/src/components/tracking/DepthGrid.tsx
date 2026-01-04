// DepthGrid.tsx - Renders depth level indicators and grid for 3D mine visualization
import { useMemo } from 'react';
import { Text, Plane } from '@react-three/drei';
import * as THREE from 'three';
import { MINE_COLORS } from '@/types/mine3d';

interface DepthGridProps {
  maxDepth: number; // Maximum depth in meters (positive number)
  levelInterval: number; // Interval between levels (e.g., 50 meters)
  gridSize: number; // Size of the grid in each direction
  showGrid: boolean;
  showDepthLabels: boolean;
  gridOpacity: number;
  scale?: number;
}

// Custom line component using native Three.js
const GridLine = ({ 
  points, 
  color, 
  opacity = 1,
}: { 
  points: THREE.Vector3[]; 
  color: string; 
  opacity?: number;
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
      />
    </line>
  );
};

// Single depth level plane
const DepthLevelPlane = ({
  depth,
  gridSize,
  color,
  showLabel,
  opacity,
  scale,
}: {
  depth: number;
  gridSize: number;
  color: string;
  showLabel: boolean;
  opacity: number;
  scale: number;
}) => {
  const y = -depth * scale;
  const size = gridSize * scale;

  // Create grid lines for this level
  const gridLines = useMemo(() => {
    const lines: THREE.Vector3[][] = [];
    const step = 20 * scale; // Grid line spacing
    const halfSize = size / 2;

    // Horizontal lines (X direction)
    for (let z = -halfSize; z <= halfSize; z += step) {
      lines.push([
        new THREE.Vector3(-halfSize, y, z),
        new THREE.Vector3(halfSize, y, z),
      ]);
    }

    // Vertical lines (Z direction)
    for (let x = -halfSize; x <= halfSize; x += step) {
      lines.push([
        new THREE.Vector3(x, y, -halfSize),
        new THREE.Vector3(x, y, halfSize),
      ]);
    }

    return lines;
  }, [y, size, scale]);

  // Border points
  const borderPoints = useMemo(() => [
    new THREE.Vector3(-size / 2, y, -size / 2),
    new THREE.Vector3(size / 2, y, -size / 2),
    new THREE.Vector3(size / 2, y, size / 2),
    new THREE.Vector3(-size / 2, y, size / 2),
    new THREE.Vector3(-size / 2, y, -size / 2),
  ], [size, y]);

  return (
    <group>
      {/* Semi-transparent plane */}
      <Plane
        args={[size, size]}
        position={[0, y, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <meshBasicMaterial
          color={color}
          transparent
          opacity={opacity * 0.1}
          side={THREE.DoubleSide}
        />
      </Plane>

      {/* Grid lines */}
      {gridLines.map((points, i) => (
        <GridLine
          key={i}
          points={points}
          color={MINE_COLORS.grid}
          opacity={opacity}
        />
      ))}

      {/* Border outline */}
      <GridLine
        points={borderPoints}
        color={color}
        opacity={opacity * 0.8}
      />

      {/* Depth label */}
      {showLabel && (
        <>
          {/* Main label */}
          <Text
            position={[-size / 2 - 5, y, 0]}
            fontSize={3}
            color={color}
            anchorX="right"
            anchorY="middle"
            rotation={[0, Math.PI / 2, 0]}
          >
            -{depth}m
          </Text>

          {/* Level name on corner */}
          <Text
            position={[-size / 2 + 2, y + 0.5, -size / 2 + 2]}
            fontSize={2}
            color={color}
            anchorX="left"
            anchorY="middle"
          >
            Level {Math.floor(depth / 50)}
          </Text>
        </>
      )}
    </group>
  );
};

// Vertical depth scale/ruler
const DepthRuler = ({
  maxDepth,
  scale,
  position,
}: {
  maxDepth: number;
  scale: number;
  position: [number, number, number];
}) => {
  const marks = useMemo(() => {
    const result: { depth: number; isMajor: boolean }[] = [];
    for (let d = 0; d <= maxDepth; d += 10) {
      result.push({ depth: d, isMajor: d % 50 === 0 });
    }
    return result;
  }, [maxDepth]);

  // Main vertical line points
  const mainLinePoints = useMemo(() => [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, -maxDepth * scale, 0),
  ], [maxDepth, scale]);

  return (
    <group position={position}>
      {/* Main vertical line */}
      <GridLine
        points={mainLinePoints}
        color={MINE_COLORS.gridMajor}
      />

      {/* Tick marks and labels */}
      {marks.map(({ depth, isMajor }) => {
        const tickPoints = [
          new THREE.Vector3(0, -depth * scale, 0),
          new THREE.Vector3(isMajor ? 2 : 1, -depth * scale, 0),
        ];
        
        return (
          <group key={depth}>
            {/* Tick mark */}
            <GridLine
              points={tickPoints}
              color={isMajor ? MINE_COLORS.gridMajor : MINE_COLORS.grid}
            />

            {/* Label for major marks */}
            {isMajor && (
              <Text
                position={[4, -depth * scale, 0]}
                fontSize={1.5}
                color="#94a3b8"
                anchorX="left"
                anchorY="middle"
              >
                {depth}m
              </Text>
            )}
          </group>
        );
      })}

      {/* "DEPTH" label at top */}
      <Text
        position={[0, 3, 0]}
        fontSize={1.5}
        color="#64748b"
        anchorX="center"
        anchorY="middle"
      >
        DEPTH
      </Text>

      {/* Surface indicator */}
      <Text
        position={[4, 0, 0]}
        fontSize={1.2}
        color="#22c55e"
        anchorX="left"
        anchorY="middle"
      >
        SURFACE
      </Text>
    </group>
  );
};

// Axis indicators
const AxisIndicators = ({
  size,
  scale,
}: {
  size: number;
  scale: number;
}) => {
  const length = size * scale * 0.6;

  // Axis line points
  const xAxisPoints = useMemo(() => [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(length, 0, 0),
  ], [length]);

  const yAxisPoints = useMemo(() => [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, -length * 0.5, 0),
  ], [length]);

  const zAxisPoints = useMemo(() => [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, 0, length),
  ], [length]);

  return (
    <group position={[0, 2, 0]}>
      {/* X axis (East-West) - Red */}
      <group>
        <GridLine points={xAxisPoints} color="#ef4444" />
        <Text
          position={[length + 2, 0, 0]}
          fontSize={1.5}
          color="#ef4444"
          anchorX="left"
        >
          E
        </Text>
      </group>

      {/* Y axis (Depth) - Green */}
      <group>
        <GridLine points={yAxisPoints} color="#22c55e" />
        <Text
          position={[0, -length * 0.5 - 2, 0]}
          fontSize={1.5}
          color="#22c55e"
        >
          ↓ DEPTH
        </Text>
      </group>

      {/* Z axis (North-South) - Blue */}
      <group>
        <GridLine points={zAxisPoints} color="#3b82f6" />
        <Text
          position={[0, 0, length + 2]}
          fontSize={1.5}
          color="#3b82f6"
        >
          N
        </Text>
      </group>

      {/* Origin marker */}
      <mesh>
        <sphereGeometry args={[0.5, 16, 16]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>
    </group>
  );
};

// Main DepthGrid component
const DepthGrid = ({
  maxDepth,
  levelInterval,
  gridSize,
  showGrid,
  showDepthLabels,
  gridOpacity,
  scale = 0.1,
}: DepthGridProps) => {
  // Generate depth levels
  const levels = useMemo(() => {
    const result: { depth: number; color: string }[] = [];
    const colors = [
      MINE_COLORS.level1,
      MINE_COLORS.level2,
      MINE_COLORS.level3,
      MINE_COLORS.level4,
      MINE_COLORS.level5,
    ];

    for (let d = levelInterval; d <= maxDepth; d += levelInterval) {
      const colorIndex = Math.floor(d / levelInterval) - 1;
      result.push({
        depth: d,
        color: colors[colorIndex % colors.length],
      });
    }

    return result;
  }, [maxDepth, levelInterval]);

  // Vertical corner pillar points
  const cornerPillarPoints = useMemo(() => {
    return [
      [-1, -1],
      [-1, 1],
      [1, -1],
      [1, 1],
    ].map(([xMult, zMult]) => [
      new THREE.Vector3(
        (gridSize * scale / 2) * xMult,
        0,
        (gridSize * scale / 2) * zMult
      ),
      new THREE.Vector3(
        (gridSize * scale / 2) * xMult,
        -maxDepth * scale,
        (gridSize * scale / 2) * zMult
      ),
    ]);
  }, [gridSize, scale, maxDepth]);

  if (!showGrid) return null;

  return (
    <group>
      {/* Surface level (y = 0) */}
      <DepthLevelPlane
        depth={0}
        gridSize={gridSize}
        color="#22c55e"
        showLabel={showDepthLabels}
        opacity={gridOpacity}
        scale={scale}
      />

      {/* Underground levels */}
      {levels.map(({ depth, color }) => (
        <DepthLevelPlane
          key={depth}
          depth={depth}
          gridSize={gridSize}
          color={color}
          showLabel={showDepthLabels}
          opacity={gridOpacity * 0.7}
          scale={scale}
        />
      ))}

      {/* Depth ruler */}
      <DepthRuler
        maxDepth={maxDepth}
        scale={scale}
        position={[-gridSize * scale / 2 - 10, 0, -gridSize * scale / 2 - 10]}
      />

      {/* Axis indicators */}
      <AxisIndicators size={gridSize} scale={scale} />

      {/* Vertical corner pillars */}
      {cornerPillarPoints.map((points, i) => (
        <GridLine
          key={i}
          points={points}
          color={MINE_COLORS.grid}
          opacity={gridOpacity * 0.5}
        />
      ))}
    </group>
  );
};

export default DepthGrid;
