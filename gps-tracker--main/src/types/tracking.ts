export interface GPSPosition {
  id: string;
  latitude: number;
  longitude: number;
  timestamp: Date;
  speed: number; // km/h
  heading: number; // degrees 0-360
  altitude?: number; // meters (negative for underground depth)
  accuracy?: number; // meters
  battery?: number; // percentage 0-100
  depth?: number; // underground depth in meters
  zone?: string; // mine zone identifier
  signalStrength?: number; // positioning signal strength 0-100
}

export interface Device {
  id: string;
  name: string;
  type: 'mining_vehicle' | 'personnel' | 'equipment';
  lastPosition: GPSPosition | null;
  isOnline: boolean;
  lastSeen: Date;
  status?: 'operational' | 'breakdown' | 'maintenance' | 'emergency';
}

export interface MineZone {
  id: string;
  name: string;
  level: number; // underground level (-1, -2, etc.)
  coordinates: { lat: number; lng: number }[];
  type: 'tunnel' | 'shaft' | 'station' | 'extraction' | 'emergency_exit';
  beaconCount?: number;
}

export interface Geofence {
  id: string;
  name: string;
  center: { lat: number; lng: number };
  radius: number; // meters
  isActive: boolean;
  alertOnEnter: boolean;
  alertOnExit: boolean;
  zoneType?: 'safe' | 'restricted' | 'hazard' | 'emergency_point';
}

export interface Alert {
  id: string;
  type: 'geofence_enter' | 'geofence_exit' | 'low_battery' | 'connection_lost' | 'speeding' | 'breakdown' | 'emergency' | 'signal_lost';
  message: string;
  timestamp: Date;
  isRead: boolean;
  deviceId: string;
  geofenceId?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  location?: { lat: number; lng: number; depth?: number };
}

export interface TrackingState {
  currentPosition: GPSPosition | null;
  trackHistory: GPSPosition[];
  device: Device | null;
  geofences: Geofence[];
  alerts: Alert[];
  isPlaying: boolean;
  playbackIndex: number;
  playbackSpeed: number;
  mineZones: MineZone[];
  isUnderground: boolean;
}