// Database types for Supabase tracking tables

export interface TrackingDevice {
  id: string;
  device_id: string;
  name: string;
  type: 'mining_vehicle' | 'personnel' | 'equipment' | 'drill';
  status: 'operational' | 'breakdown' | 'maintenance' | 'emergency' | 'offline';
  battery_level: number;
  is_online: boolean;
  last_seen_at: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TrackingPosition {
  id: string;
  device_id: string;
  latitude: number;
  longitude: number;
  depth: number;
  altitude: number;
  speed: number;
  heading: number;
  accuracy: number;
  signal_strength: number;
  zone: string | null;
  timestamp: string;
  raw_data: Record<string, unknown>;
}

export interface TrackingAlert {
  id: string;
  device_id: string;
  type: 'emergency' | 'breakdown' | 'geofence_enter' | 'geofence_exit' | 'low_battery' | 'signal_lost' | 'speeding' | 'offline';
  priority: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  latitude: number | null;
  longitude: number | null;
  depth: number | null;
  zone: string | null;
  is_read: boolean;
  is_resolved: boolean;
  resolved_at: string | null;
  resolved_by: string | null;
  created_at: string;
}

export interface TrackingZone {
  id: string;
  name: string;
  type: 'safe' | 'restricted' | 'hazard' | 'emergency_point' | 'tunnel' | 'shaft' | 'extraction';
  level: number;
  center_lat: number;
  center_lng: number;
  radius: number;
  depth_min: number;
  depth_max: number;
  alert_on_enter: boolean;
  alert_on_exit: boolean;
  is_active: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
}

// Insert types (for creating new records)
export type TrackingPositionInsert = Omit<TrackingPosition, 'id' | 'timestamp'> & {
  timestamp?: string;
};

export type TrackingAlertInsert = Omit<TrackingAlert, 'id' | 'created_at' | 'is_read' | 'is_resolved' | 'resolved_at' | 'resolved_by'>;

