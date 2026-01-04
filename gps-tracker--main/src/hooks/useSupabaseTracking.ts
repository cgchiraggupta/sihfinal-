import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/lib/supabase';
import { TrackingDevice, TrackingPosition, TrackingAlert, TrackingZone, TrackingPositionInsert, TrackingAlertInsert } from '@/types/database';
import { GPSPosition, Device, Geofence, Alert } from '@/types/tracking';
import { mineLayout } from '@/data/mineLayout3D';

interface UseSupabaseTrackingOptions {
  selectedDeviceId?: string;
  simulationMode?: boolean;
}

export const useSupabaseTracking = (options: UseSupabaseTrackingOptions = {}) => {
  const { selectedDeviceId, simulationMode = false } = options;
  
  // State
  const [devices, setDevices] = useState<TrackingDevice[]>([]);
  const [currentDevice, setCurrentDevice] = useState<Device | null>(null);
  const [currentPosition, setCurrentPosition] = useState<GPSPosition | null>(null);
  const [trackHistory, setTrackHistory] = useState<GPSPosition[]>([]);
  const [allDevicePositions, setAllDevicePositions] = useState<Map<string, GPSPosition>>(new Map());
  const [allDeviceTrackHistory, setAllDeviceTrackHistory] = useState<Map<string, GPSPosition[]>>(new Map());
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [geofences, setGeofences] = useState<Geofence[]>([]);
  const [zones, setZones] = useState<TrackingZone[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  
  // Refs
  const simulationRef = useRef<NodeJS.Timeout | null>(null);
  const positionChannelRef = useRef<ReturnType<typeof supabase.channel> | null>(null);
  const simulationStateRef = useRef<Map<string, {
    pathIndex: number;
    progress: number;
  }>>(new Map());

  // Convert DB position to GPSPosition
  const toGPSPosition = (pos: TrackingPosition): GPSPosition => ({
    id: pos.id,
    latitude: pos.latitude,
    longitude: pos.longitude,
    timestamp: new Date(pos.timestamp),
    speed: pos.speed,
    heading: pos.heading,
    altitude: pos.altitude,
    accuracy: pos.accuracy,
    battery: 85,
    depth: pos.depth,
    zone: pos.zone || 'Unknown',
    signalStrength: pos.signal_strength,
  });

  // Convert DB device to Device
  const toDevice = (dev: TrackingDevice): Device => ({
    id: dev.id,
    name: dev.name,
    type: dev.type as Device['type'],
    lastPosition: null,
    isOnline: dev.is_online,
    lastSeen: dev.last_seen_at ? new Date(dev.last_seen_at) : new Date(),
    status: dev.status as Device['status'],
  });

  // Convert DB zone to Geofence
  const toGeofence = (zone: TrackingZone): Geofence => ({
    id: zone.id,
    name: zone.name,
    center: { lat: zone.center_lat, lng: zone.center_lng },
    radius: zone.radius,
    isActive: zone.is_active,
    alertOnEnter: zone.alert_on_enter,
    alertOnExit: zone.alert_on_exit,
    zoneType: zone.type as Geofence['zoneType'],
  });

  // Convert DB alert to Alert
  const toAlert = (dbAlert: TrackingAlert): Alert => ({
    id: dbAlert.id,
    type: dbAlert.type as Alert['type'],
    message: dbAlert.message,
    timestamp: new Date(dbAlert.created_at),
    isRead: dbAlert.is_read,
    deviceId: dbAlert.device_id,
    priority: dbAlert.priority as Alert['priority'],
    location: dbAlert.latitude && dbAlert.longitude ? {
      lat: dbAlert.latitude,
      lng: dbAlert.longitude,
      depth: dbAlert.depth || undefined,
    } : undefined,
  });

  // Fetch initial data
  const fetchInitialData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch devices
      const { data: devicesData, error: devicesError } = await supabase
        .from('tracking_devices')
        .select('*')
        .order('name');
      
      if (devicesError) throw devicesError;
      setDevices(devicesData || []);

      // Fetch zones
      const { data: zonesData, error: zonesError } = await supabase
        .from('tracking_zones')
        .select('*')
        .eq('is_active', true);
      
      if (zonesError) throw zonesError;
      setZones(zonesData || []);
      setGeofences((zonesData || []).map(toGeofence));

      // If device selected, fetch its data
      if (selectedDeviceId) {
        const device = devicesData?.find(d => d.id === selectedDeviceId);
        if (device) {
          setCurrentDevice(toDevice(device));
          
          // Fetch position history
          const { data: positionsData, error: positionsError } = await supabase
            .from('tracking_positions')
            .select('*')
            .eq('device_id', selectedDeviceId)
            .order('timestamp', { ascending: false })
            .limit(200);
          
          if (positionsError) throw positionsError;
          
          const positions = (positionsData || []).reverse().map(toGPSPosition);
          setTrackHistory(positions);
          if (positions.length > 0) {
            setCurrentPosition(positions[positions.length - 1]);
          }
        }
      } else if (devicesData && devicesData.length > 0) {
        // Auto-select first device
        const firstDevice = devicesData[0];
        setCurrentDevice(toDevice(firstDevice));
      }

      // Fetch unread alerts
      const { data: alertsData, error: alertsError } = await supabase
        .from('tracking_alerts')
        .select('*')
        .eq('is_resolved', false)
        .order('created_at', { ascending: false })
        .limit(50);
      
      if (alertsError) throw alertsError;
      setAlerts((alertsData || []).map(toAlert));

    } catch (err) {
      console.error('Error fetching tracking data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setIsLoading(false);
    }
  }, [selectedDeviceId]);

  // Subscribe to real-time updates
  const subscribeToRealtime = useCallback(() => {
    // Subscribe to position updates
    positionChannelRef.current = supabase
      .channel('tracking_positions_changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'tracking_positions',
        },
        (payload) => {
          const newPosition = payload.new as TrackingPosition;
          const gpsPosition = toGPSPosition(newPosition);
          
          // Update all device positions map
          setAllDevicePositions(prev => {
            const updated = new Map(prev);
            updated.set(newPosition.device_id, gpsPosition);
            return updated;
          });
          
          // Update track history for all devices
          setAllDeviceTrackHistory(prev => {
            const updated = new Map(prev);
            const deviceHistory = updated.get(newPosition.device_id) || [];
            updated.set(newPosition.device_id, [...deviceHistory.slice(-199), gpsPosition]);
            return updated;
          });
          
          // Update if it's for the selected device
          if (!selectedDeviceId || newPosition.device_id === selectedDeviceId) {
            setCurrentPosition(gpsPosition);
            setTrackHistory(prev => [...prev.slice(-199), gpsPosition]);
          }
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'tracking_alerts',
        },
        (payload) => {
          const newAlert = payload.new as TrackingAlert;
          setAlerts(prev => [toAlert(newAlert), ...prev].slice(0, 50));
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'tracking_devices',
        },
        (payload) => {
          const updatedDevice = payload.new as TrackingDevice;
          setDevices(prev => prev.map(d => d.id === updatedDevice.id ? updatedDevice : d));
          
          if (selectedDeviceId === updatedDevice.id || currentDevice?.id === updatedDevice.id) {
            setCurrentDevice(toDevice(updatedDevice));
          }
        }
      )
      .subscribe();
  }, [selectedDeviceId, currentDevice?.id]);

  // ================== SIMULATION MODE ==================
  
  // Create different paths for different drills
  const createTunnelPath = useCallback((pathType: 'path1' | 'path2' | 'path3' = 'path1') => {
    // Path 1: Main route through all levels
    const route1: string[] = [
      'surf_entry', 'shaft_l1', 'l1_n1', 'l1_n2', 'l1_n1', 'shaft_l1',
      'shaft_l2', 'l2_n1', 'l2_n2', 'l2_n1', 'l2_cross_1', 'l2_cross_2',
      'l2_cross_1', 'shaft_l2', 'shaft_l3', 'l3_n1', 'l3_n2', 'l3_n1',
      'l3_n3', 'l3_n4', 'l3_n3', 'shaft_l3', 'shaft_l2', 'shaft_l1', 'surf_entry',
    ];
    
    // Path 2: Level 1 and Level 2 focus
    const route2: string[] = [
      'surf_entry', 'shaft_l1', 'l1_n3', 'l1_n4', 'l1_n3', 'l1_loop_1',
      'l1_loop_2', 'shaft_l1', 'shaft_l2', 'l2_n3', 'l2_n4', 'l2_n3',
      'shaft_l2', 'shaft_l1', 'surf_entry',
    ];
    
    // Path 3: Deep exploration focus
    const route3: string[] = [
      'surf_entry', 'shaft_l1', 'shaft_l2', 'shaft_l3', 'l3_n3', 'l3_n4',
      'l3_n3', 'l3_n1', 'l3_n2', 'l3_n1', 'shaft_l3', 'shaft_l2',
      'l2_cross_1', 'l2_cross_2', 'l2_cross_1', 'shaft_l2', 'shaft_l1', 'surf_entry',
    ];
    
    const route = pathType === 'path1' ? route1 : pathType === 'path2' ? route2 : route3;
    
    return route.map(nodeId => {
      const node = mineLayout.nodes.find(n => n.id === nodeId);
      if (!node) return null;
      
      // Convert node position to GPS coordinates
      const dLat = node.position.z / 111320; // z is north-south
      const dLng = node.position.x / 103000;  // x is east-west
      
      return {
        nodeId,
        lat: mineLayout.centerReference.lat - dLat,
        lng: mineLayout.centerReference.lng + dLng,
        depth: -node.position.y, // y is depth (negative)
        position: node.position
      };
    }).filter(Boolean) as Array<{
      nodeId: string;
      lat: number;
      lng: number;
      depth: number;
      position: { x: number; y: number; z: number };
    }>;
  }, []);
  
  const startSimulation = useCallback(async () => {
    if (devices.length === 0) return;
    
    setIsSimulating(true);
    
    // Get up to 3 drill devices (prioritize drills, then any device)
    // Always simulate at least 2-3 devices for visibility
    const drillDevices = devices
      .filter(d => d.type === 'drill' || d.name.toLowerCase().includes('drill') || d.name.toLowerCase().includes('simba'))
      .slice(0, 3);
    
    // If we have at least 2 drills, use them. Otherwise, use first 3 devices (or all if less than 3)
    let devicesToSimulate: TrackingDevice[];
    if (drillDevices.length >= 2) {
      devicesToSimulate = drillDevices;
    } else if (drillDevices.length === 1 && devices.length >= 2) {
      // If only 1 drill, add more devices to reach at least 2
      const otherDevices = devices.filter(d => !drillDevices.includes(d)).slice(0, 2);
      devicesToSimulate = [...drillDevices, ...otherDevices].slice(0, 3);
    } else {
      // Use first 3 devices (or all if less than 3)
      devicesToSimulate = devices.slice(0, Math.min(3, devices.length));
    }
    
    if (devicesToSimulate.length === 0) {
      console.warn('No devices to simulate');
      return;
    }
    
    console.log(`Simulating ${devicesToSimulate.length} devices:`, devicesToSimulate.map(d => d.name));
    
    // Create paths for each device
    const devicePaths = devicesToSimulate.map((device, index) => {
      const pathType = index === 0 ? 'path1' : index === 1 ? 'path2' : 'path3';
      return {
        deviceId: device.id,
        device,
        path: createTunnelPath(pathType),
        pathType
      };
    });
    
    // Initialize simulation state for each device
    devicePaths.forEach(({ deviceId }) => {
      if (!simulationStateRef.current.has(deviceId)) {
        simulationStateRef.current.set(deviceId, { pathIndex: 0, progress: 0 });
      }
    });
    
    const speed = 8; // km/h - speed through tunnels
    
    const simulatePosition = async () => {
      // Simulate each device
      for (const { deviceId, device, path } of devicePaths) {
        const state = simulationStateRef.current.get(deviceId);
        if (!state || path.length === 0) continue;
        
        const currentPoint = path[state.pathIndex];
        const nextPoint = path[(state.pathIndex + 1) % path.length];
        
        if (!currentPoint || !nextPoint) continue;
        
        // Calculate distance between nodes
        const dx = nextPoint.position.x - currentPoint.position.x;
        const dy = nextPoint.position.y - currentPoint.position.y;
        const dz = nextPoint.position.z - currentPoint.position.z;
        const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
        
        // Calculate heading (direction to next node)
        const heading = Math.atan2(dx, dz) * (180 / Math.PI);
        const normalizedHeading = heading < 0 ? heading + 360 : heading;
        
        // Move along the path
        const moveDistance = (speed / 3600) * 2; // Distance in ~2 seconds (meters)
        const segmentLength = distance;
        const moveProgress = moveDistance / segmentLength;
        
        state.progress += moveProgress;
        
        let lat: number, lng: number, depth: number;
        
        // If we've reached the next node, move to it
        if (state.progress >= 1) {
          state.progress = 0;
          state.pathIndex = (state.pathIndex + 1) % path.length;
          
          const targetPoint = path[state.pathIndex];
          if (!targetPoint) continue;
          
          lat = targetPoint.lat;
          lng = targetPoint.lng;
          depth = targetPoint.depth;
        } else {
          // Interpolate between current and next node
          lat = currentPoint.lat + (nextPoint.lat - currentPoint.lat) * state.progress;
          lng = currentPoint.lng + (nextPoint.lng - currentPoint.lng) * state.progress;
          depth = currentPoint.depth + (nextPoint.depth - currentPoint.depth) * state.progress;
        }
        
        // Determine zone based on depth
        let zone = 'Surface';
        if (depth > 200) zone = 'Level 3 - Deep Extraction';
        else if (depth > 100) zone = 'Level 2 - Production';
        else if (depth > 30) zone = 'Level 1 - Logistics';
        else if (depth > 0) zone = 'Main Shaft';
        
        // Signal degrades with depth (leaky feeder simulation)
        const signalStrength = Math.max(5, 100 - (depth / 3) - Math.random() * 5);
        
        const positionData: TrackingPositionInsert = {
          device_id: deviceId,
          latitude: lat,
          longitude: lng,
          depth,
          altitude: -depth,
          speed: speed + Math.random() * 2, // 8-10 km/h
          heading: normalizedHeading,
          accuracy: 5 + depth * 0.05,
          signal_strength: Math.round(signalStrength),
          zone,
          raw_data: { simulated: true, timestamp: Date.now(), is_underground: depth > 5 },
        };
        
        // Insert into Supabase
        const { error } = await supabase
          .from('tracking_positions')
          .insert(positionData);
        
        if (error) {
          console.error('Simulation insert error:', error);
        }
        
        // Update device last_seen
        await supabase
          .from('tracking_devices')
          .update({ 
            is_online: true, 
            last_seen_at: new Date().toISOString(),
            battery_level: Math.max(10, 85 - Math.floor(Math.random() * 5)),
          })
          .eq('id', deviceId);
      }
    };
    
    // Run simulation every 2 seconds
    simulationRef.current = setInterval(simulatePosition, 2000);
    simulatePosition(); // Run immediately
  }, [devices, createTunnelPath]);

  const stopSimulation = useCallback(() => {
    if (simulationRef.current) {
      clearInterval(simulationRef.current);
      simulationRef.current = null;
    }
    setIsSimulating(false);
    // Reset simulation state for all devices
    simulationStateRef.current.clear();
  }, []);

  // ================== ACTIONS ==================

  const triggerEmergency = useCallback(async () => {
    if (!currentDevice || !currentPosition) return;

    const alertData: TrackingAlertInsert = {
      device_id: currentDevice.id,
      type: 'emergency',
      priority: 'critical',
      message: `EMERGENCY: ${currentDevice.name} - Emergency at ${currentPosition.zone || 'Unknown Zone'}`,
      latitude: currentPosition.latitude,
      longitude: currentPosition.longitude,
      depth: currentPosition.depth,
      zone: currentPosition.zone,
    };

    const { error } = await supabase.from('tracking_alerts').insert(alertData);
    if (error) console.error('Error creating emergency alert:', error);

    // Update device status
    await supabase
      .from('tracking_devices')
      .update({ status: 'emergency' })
      .eq('id', currentDevice.id);
  }, [currentDevice, currentPosition]);

  const reportBreakdown = useCallback(async () => {
    if (!currentDevice || !currentPosition) return;

    const alertData: TrackingAlertInsert = {
      device_id: currentDevice.id,
      type: 'breakdown',
      priority: 'high',
      message: `BREAKDOWN: ${currentDevice.name} requires assistance at ${currentPosition.zone || 'Unknown Zone'}`,
      latitude: currentPosition.latitude,
      longitude: currentPosition.longitude,
      depth: currentPosition.depth,
      zone: currentPosition.zone,
    };

    const { error } = await supabase.from('tracking_alerts').insert(alertData);
    if (error) console.error('Error creating breakdown alert:', error);

    // Update device status
    await supabase
      .from('tracking_devices')
      .update({ status: 'breakdown' })
      .eq('id', currentDevice.id);
  }, [currentDevice, currentPosition]);

  const clearEmergency = useCallback(async () => {
    if (!currentDevice) return;

    await supabase
      .from('tracking_devices')
      .update({ status: 'operational' })
      .eq('id', currentDevice.id);
  }, [currentDevice]);

  const dismissAlert = useCallback(async (alertId: string) => {
    await supabase
      .from('tracking_alerts')
      .update({ is_read: true })
      .eq('id', alertId);

    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, isRead: true } : a));
  }, []);

  const selectDevice = useCallback((deviceId: string) => {
    const device = devices.find(d => d.id === deviceId);
    if (device) {
      setCurrentDevice(toDevice(device));
      // Fetch positions for this device
      fetchInitialData();
    }
  }, [devices, fetchInitialData]);

  // ================== EFFECTS ==================

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  useEffect(() => {
    subscribeToRealtime();
    
    return () => {
      positionChannelRef.current?.unsubscribe();
    };
  }, [subscribeToRealtime]);

  // Auto-start/stop simulation based on mode
  useEffect(() => {
    if (simulationMode && currentDevice) {
      startSimulation();
    } else {
      stopSimulation();
    }
    
    return () => {
      stopSimulation();
    };
  }, [simulationMode, currentDevice, startSimulation, stopSimulation]);

  // Derived state
  const isUnderground = (currentPosition?.depth || 0) > 10;
  const isEmergencyActive = currentDevice?.status === 'emergency' || currentDevice?.status === 'breakdown';

  return {
    // Data
    devices,
    currentDevice,
    currentPosition,
    trackHistory,
    allDevicePositions,
    allDeviceTrackHistory,
    alerts,
    geofences,
    zones,
    
    // State
    isLoading,
    error,
    isSimulating,
    isUnderground,
    isEmergencyActive,
    
    // Actions
    selectDevice,
    triggerEmergency,
    reportBreakdown,
    clearEmergency,
    dismissAlert,
    startSimulation,
    stopSimulation,
    refetch: fetchInitialData,
  };
};

