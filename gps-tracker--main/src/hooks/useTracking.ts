import { useState, useEffect, useCallback, useRef } from 'react';
import { GPSPosition, Device, Geofence, Alert, TrackingState, MineZone } from '@/types/tracking';

const miningVehicle: Device = {
  id: 'vehicle-001',
  name: 'Mining Truck #1',
  type: 'mining_vehicle',
  lastPosition: null,
  isOnline: true,
  lastSeen: new Date(),
  status: 'operational',
};

// Simulated mine zones around current position
const createMineZones = (lat: number, lng: number): MineZone[] => [
  {
    id: 'zone-main-tunnel',
    name: 'Main Tunnel',
    level: -1,
    coordinates: [
      { lat: lat - 0.001, lng: lng - 0.002 },
      { lat: lat + 0.001, lng: lng + 0.002 },
    ],
    type: 'tunnel',
    beaconCount: 8,
  },
  {
    id: 'zone-extraction',
    name: 'Extraction Zone A',
    level: -2,
    coordinates: [
      { lat: lat - 0.0005, lng: lng - 0.001 },
      { lat: lat + 0.0005, lng: lng + 0.001 },
    ],
    type: 'extraction',
    beaconCount: 4,
  },
  {
    id: 'zone-shaft',
    name: 'Main Shaft',
    level: 0,
    coordinates: [
      { lat, lng },
    ],
    type: 'shaft',
    beaconCount: 2,
  },
  {
    id: 'zone-emergency',
    name: 'Emergency Exit',
    level: -1,
    coordinates: [
      { lat: lat + 0.002, lng: lng + 0.001 },
    ],
    type: 'emergency_exit',
    beaconCount: 1,
  },
];

const createMineGeofences = (lat: number, lng: number): Geofence[] => [
  {
    id: 'geofence-safe-zone',
    name: 'Safe Zone - Surface',
    center: { lat, lng },
    radius: 200,
    isActive: true,
    alertOnEnter: false,
    alertOnExit: true,
    zoneType: 'safe',
  },
  {
    id: 'geofence-hazard',
    name: 'Hazard Zone - Blasting Area',
    center: { lat: lat - 0.001, lng: lng - 0.001 },
    radius: 100,
    isActive: true,
    alertOnEnter: true,
    alertOnExit: false,
    zoneType: 'hazard',
  },
  {
    id: 'geofence-emergency',
    name: 'Emergency Rally Point',
    center: { lat: lat + 0.002, lng: lng + 0.001 },
    radius: 50,
    isActive: true,
    alertOnEnter: false,
    alertOnExit: false,
    zoneType: 'emergency_point',
  },
];

export const useTracking = () => {
  const [state, setState] = useState<TrackingState>({
    currentPosition: null,
    trackHistory: [],
    device: miningVehicle,
    geofences: [],
    alerts: [],
    isPlaying: false,
    playbackIndex: -1,
    playbackSpeed: 1,
    mineZones: [],
    isUnderground: false,
  });

  const [locationError, setLocationError] = useState<string | null>(null);
  const [isLocating, setIsLocating] = useState(true);
  const playbackRef = useRef<NodeJS.Timeout | null>(null);
  const watchIdRef = useRef<number | null>(null);
  const initialPositionSet = useRef(false);

  // Simulate underground depth based on movement patterns
  const calculateDepth = useCallback((accuracy: number, history: GPSPosition[]): number => {
    // Simulate depth changes based on accuracy degradation (underground = worse GPS signal)
    if (accuracy > 50) {
      // Poor accuracy = likely underground
      const baseDepth = Math.min(accuracy / 2, 200);
      const variation = Math.sin(Date.now() / 10000) * 20;
      return Math.round(baseDepth + variation);
    }
    return 0;
  }, []);

  // Calculate signal strength based on accuracy
  const calculateSignalStrength = useCallback((accuracy: number, depth: number): number => {
    // Signal degrades with depth and accuracy
    const baseSignal = Math.max(0, 100 - accuracy);
    const depthPenalty = depth * 0.3;
    return Math.max(5, Math.round(baseSignal - depthPenalty));
  }, []);

  // Determine current zone based on position
  const determineZone = useCallback((lat: number, lng: number, zones: MineZone[]): string => {
    // Simple zone detection based on proximity
    for (const zone of zones) {
      const center = zone.coordinates[0];
      const distance = getDistance(lat, lng, center.lat, center.lng);
      if (distance < 100) {
        return zone.name;
      }
    }
    return 'Surface';
  }, []);

  // Use browser Geolocation API with underground simulation
  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser');
      setIsLocating(false);
      return;
    }

    const handlePosition = (position: GeolocationPosition) => {
      setIsLocating(false);
      setLocationError(null);

      setState(prev => {
        if (prev.isPlaying) return prev;

        // Calculate simulated underground metrics
        const depth = calculateDepth(position.coords.accuracy, prev.trackHistory);
        const signalStrength = calculateSignalStrength(position.coords.accuracy, depth);
        const isUnderground = depth > 10;

        // Initialize zones around first position
        let mineZones = prev.mineZones;
        let geofences = prev.geofences;
        
        if (!initialPositionSet.current) {
          initialPositionSet.current = true;
          mineZones = createMineZones(position.coords.latitude, position.coords.longitude);
          geofences = createMineGeofences(position.coords.latitude, position.coords.longitude);
        }

        const zone = determineZone(position.coords.latitude, position.coords.longitude, mineZones);

        const newPosition: GPSPosition = {
          id: `pos-${Date.now()}`,
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          timestamp: new Date(position.timestamp),
          speed: position.coords.speed ? position.coords.speed * 3.6 : 0,
          heading: position.coords.heading || 0,
          altitude: position.coords.altitude || 0,
          accuracy: position.coords.accuracy,
          battery: 85, // Simulated vehicle battery
          depth,
          zone,
          signalStrength,
        };

        const newHistory = [...prev.trackHistory.slice(-199), newPosition];
        
        // Check geofence violations and generate alerts
        const newAlerts = [...prev.alerts];
        const lastPos = prev.currentPosition;
        
        geofences.forEach(fence => {
          if (!fence.isActive || !lastPos) return;
          
          const currentDistance = getDistance(
            fence.center.lat, fence.center.lng,
            newPosition.latitude, newPosition.longitude
          );
          
          const wasInside = getDistance(
            fence.center.lat, fence.center.lng,
            lastPos.latitude, lastPos.longitude
          ) <= fence.radius;
          
          const isInside = currentDistance <= fence.radius;
          
          if (wasInside && !isInside && fence.alertOnExit) {
            newAlerts.unshift({
              id: `alert-${Date.now()}`,
              type: 'geofence_exit',
              message: `${prev.device?.name} left ${fence.name}`,
              timestamp: new Date(),
              isRead: false,
              deviceId: prev.device?.id || '',
              geofenceId: fence.id,
              priority: fence.zoneType === 'safe' ? 'high' : 'medium',
              location: { lat: newPosition.latitude, lng: newPosition.longitude, depth },
            });
          }
          
          if (!wasInside && isInside && fence.alertOnEnter) {
            newAlerts.unshift({
              id: `alert-${Date.now()}`,
              type: 'geofence_enter',
              message: `${prev.device?.name} entered ${fence.name}`,
              timestamp: new Date(),
              isRead: false,
              deviceId: prev.device?.id || '',
              geofenceId: fence.id,
              priority: fence.zoneType === 'hazard' ? 'critical' : 'low',
              location: { lat: newPosition.latitude, lng: newPosition.longitude, depth },
            });
          }
        });

        // Check for signal loss alerts
        if (signalStrength < 20 && prev.currentPosition?.signalStrength && prev.currentPosition.signalStrength >= 20) {
          newAlerts.unshift({
            id: `alert-${Date.now()}-signal`,
            type: 'signal_lost',
            message: `Low signal for ${prev.device?.name} - Position may be inaccurate`,
            timestamp: new Date(),
            isRead: false,
            deviceId: prev.device?.id || '',
            priority: 'high',
            location: { lat: newPosition.latitude, lng: newPosition.longitude, depth },
          });
        }

        return {
          ...prev,
          currentPosition: newPosition,
          trackHistory: newHistory,
          geofences,
          mineZones,
          isUnderground,
          alerts: newAlerts.slice(0, 50),
          device: {
            ...prev.device!,
            lastPosition: newPosition,
            lastSeen: new Date(),
            isOnline: true,
          },
        };
      });
    };

    const handleError = (error: GeolocationPositionError) => {
      setIsLocating(false);
      switch (error.code) {
        case error.PERMISSION_DENIED:
          setLocationError('Location permission denied. Please enable location access.');
          break;
        case error.POSITION_UNAVAILABLE:
          setLocationError('Location information is unavailable.');
          break;
        case error.TIMEOUT:
          setLocationError('Location request timed out.');
          break;
        default:
          setLocationError('An unknown error occurred.');
      }
    };

    watchIdRef.current = navigator.geolocation.watchPosition(
      handlePosition,
      handleError,
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 1000,
      }
    );

    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, [calculateDepth, calculateSignalStrength, determineZone]);

  const triggerEmergency = useCallback(() => {
    setState(prev => {
      if (!prev.currentPosition) return prev;
      
      const emergencyAlert: Alert = {
        id: `alert-emergency-${Date.now()}`,
        type: 'emergency',
        message: `EMERGENCY: ${prev.device?.name} - Breakdown/Emergency at ${prev.currentPosition.zone || 'Unknown Zone'}`,
        timestamp: new Date(),
        isRead: false,
        deviceId: prev.device?.id || '',
        priority: 'critical',
        location: {
          lat: prev.currentPosition.latitude,
          lng: prev.currentPosition.longitude,
          depth: prev.currentPosition.depth,
        },
      };

      return {
        ...prev,
        alerts: [emergencyAlert, ...prev.alerts].slice(0, 50),
        device: prev.device ? { ...prev.device, status: 'emergency' } : null,
      };
    });
  }, []);

  const reportBreakdown = useCallback(() => {
    setState(prev => {
      if (!prev.currentPosition) return prev;
      
      const breakdownAlert: Alert = {
        id: `alert-breakdown-${Date.now()}`,
        type: 'breakdown',
        message: `BREAKDOWN: ${prev.device?.name} requires assistance at ${prev.currentPosition.zone || 'Unknown Zone'}`,
        timestamp: new Date(),
        isRead: false,
        deviceId: prev.device?.id || '',
        priority: 'high',
        location: {
          lat: prev.currentPosition.latitude,
          lng: prev.currentPosition.longitude,
          depth: prev.currentPosition.depth,
        },
      };

      return {
        ...prev,
        alerts: [breakdownAlert, ...prev.alerts].slice(0, 50),
        device: prev.device ? { ...prev.device, status: 'breakdown' } : null,
      };
    });
  }, []);

  const clearEmergency = useCallback(() => {
    setState(prev => ({
      ...prev,
      device: prev.device ? { ...prev.device, status: 'operational' } : null,
    }));
  }, []);

  const startPlayback = useCallback(() => {
    setState(prev => ({
      ...prev,
      isPlaying: true,
      playbackIndex: 0,
    }));
  }, []);

  const stopPlayback = useCallback(() => {
    if (playbackRef.current) {
      clearInterval(playbackRef.current);
      playbackRef.current = null;
    }
    setState(prev => ({
      ...prev,
      isPlaying: false,
      playbackIndex: -1,
      currentPosition: prev.trackHistory[prev.trackHistory.length - 1] || null,
    }));
  }, []);

  const setPlaybackIndex = useCallback((index: number) => {
    setState(prev => {
      const pos = prev.trackHistory[index];
      return {
        ...prev,
        playbackIndex: index,
        currentPosition: pos || prev.currentPosition,
      };
    });
  }, []);

  const setPlaybackSpeed = useCallback((speed: number) => {
    setState(prev => ({ ...prev, playbackSpeed: speed }));
  }, []);

  useEffect(() => {
    if (state.isPlaying && state.playbackIndex >= 0) {
      playbackRef.current = setInterval(() => {
        setState(prev => {
          const nextIndex = prev.playbackIndex + 1;
          if (nextIndex >= prev.trackHistory.length) {
            return {
              ...prev,
              isPlaying: false,
              playbackIndex: prev.trackHistory.length - 1,
            };
          }
          return {
            ...prev,
            playbackIndex: nextIndex,
            currentPosition: prev.trackHistory[nextIndex],
          };
        });
      }, 1000 / state.playbackSpeed);
    } else if (playbackRef.current) {
      clearInterval(playbackRef.current);
      playbackRef.current = null;
    }

    return () => {
      if (playbackRef.current) clearInterval(playbackRef.current);
    };
  }, [state.isPlaying, state.playbackSpeed]);

  const dismissAlert = useCallback((alertId: string) => {
    setState(prev => ({
      ...prev,
      alerts: prev.alerts.map(a => 
        a.id === alertId ? { ...a, isRead: true } : a
      ),
    }));
  }, []);

  const addGeofence = useCallback((geofence: Omit<Geofence, 'id'>) => {
    setState(prev => ({
      ...prev,
      geofences: [...prev.geofences, { ...geofence, id: `geofence-${Date.now()}` }],
    }));
  }, []);

  return {
    ...state,
    locationError,
    isLocating,
    startPlayback,
    stopPlayback,
    setPlaybackIndex,
    setPlaybackSpeed,
    dismissAlert,
    addGeofence,
    triggerEmergency,
    reportBreakdown,
    clearEmergency,
  };
};

function getDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000;
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lon2 - lon1) * Math.PI / 180;

  const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ/2) * Math.sin(Δλ/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

  return R * c;
}