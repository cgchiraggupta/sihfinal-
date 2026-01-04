import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { GPSPosition, Geofence, MineZone } from '@/types/tracking';

interface TrackingMapProps {
  currentPosition: GPSPosition | null;
  trackHistory: GPSPosition[];
  geofences: Geofence[];
  playbackIndex?: number;
  mineZones?: MineZone[];
  isUnderground?: boolean;
}

const TrackingMap = ({ 
  currentPosition, 
  trackHistory, 
  geofences,
  playbackIndex = -1,
  mineZones = [],
  isUnderground = false,
}: TrackingMapProps) => {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const polylineRef = useRef<L.Polyline | null>(null);
  const glowPolylineRef = useRef<L.Polyline | null>(null);
  const geofenceLayersRef = useRef<L.Circle[]>([]);
  const zoneLayersRef = useRef<L.Layer[]>([]);

  // Initialize map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const center: [number, number] = currentPosition 
      ? [currentPosition.latitude, currentPosition.longitude]
      : [40.7128, -74.006];

    mapRef.current = L.map(containerRef.current, {
      center,
      zoom: 17,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
    }).addTo(mapRef.current);

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Update mine zone overlays
  useEffect(() => {
    if (!mapRef.current) return;

    // Remove existing zone layers
    zoneLayersRef.current.forEach(layer => {
      mapRef.current?.removeLayer(layer);
    });
    zoneLayersRef.current = [];

    // Add mine zone markers
    mineZones.forEach(zone => {
      if (!mapRef.current || !zone.coordinates[0]) return;

      const getZoneColor = (type: MineZone['type']) => {
        switch (type) {
          case 'tunnel': return '#3b82f6';
          case 'shaft': return '#8b5cf6';
          case 'extraction': return '#f59e0b';
          case 'station': return '#10b981';
          case 'emergency_exit': return '#ef4444';
          default: return '#6b7280';
        }
      };

      const color = getZoneColor(zone.type);

      // Add zone marker
      const icon = L.divIcon({
        className: 'mine-zone-marker',
        html: `
          <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            transform: translateY(-50%);
          ">
            <div style="
              background: ${color};
              color: white;
              padding: 4px 8px;
              border-radius: 4px;
              font-size: 10px;
              font-weight: bold;
              white-space: nowrap;
              box-shadow: 0 2px 8px rgba(0,0,0,0.5);
            ">
              ${zone.name}
            </div>
            <div style="
              width: 2px;
              height: 12px;
              background: ${color};
            "></div>
            <div style="
              width: 8px;
              height: 8px;
              background: ${color};
              border-radius: 50%;
              box-shadow: 0 0 10px ${color};
            "></div>
          </div>
        `,
        iconSize: [100, 50],
        iconAnchor: [50, 50],
      });

      const marker = L.marker([zone.coordinates[0].lat, zone.coordinates[0].lng], { icon })
        .addTo(mapRef.current);
      zoneLayersRef.current.push(marker);

      // Add zone area for tunnels
      if (zone.type === 'tunnel' && zone.coordinates.length > 1) {
        const line = L.polyline(
          zone.coordinates.map(c => [c.lat, c.lng] as [number, number]),
          {
            color,
            weight: 12,
            opacity: 0.3,
            lineCap: 'round',
          }
        ).addTo(mapRef.current);
        zoneLayersRef.current.push(line);
      }
    });
  }, [mineZones]);

  // Update marker position
  useEffect(() => {
    if (!mapRef.current || !currentPosition) return;

    const heading = currentPosition.heading || 0;
    const isEmergency = (currentPosition as any).emergency;
    const markerColor = isUnderground ? 'rgb(245, 158, 11)' : 'rgb(14, 184, 195)';
    const pulseColor = isUnderground ? 'rgba(245, 158, 11, 0.3)' : 'rgba(14, 184, 195, 0.3)';
    
    const icon = L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="
          width: 56px;
          height: 56px;
          position: relative;
          transform: rotate(${heading}deg);
        ">
          <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            width: 56px;
            height: 56px;
            margin: -28px;
            border-radius: 50%;
            background: radial-gradient(circle, ${pulseColor} 0%, transparent 70%);
            animation: pulse-ring 2s ease-out infinite;
          "></div>
          <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            width: 40px;
            height: 40px;
            margin: -20px;
            border-radius: 50%;
            background: radial-gradient(circle, ${pulseColor} 0%, transparent 60%);
          "></div>
          <!-- Mining truck icon -->
          <svg 
            viewBox="0 0 24 24" 
            style="
              position: absolute;
              top: 50%;
              left: 50%;
              width: 32px;
              height: 32px;
              margin: -16px;
              filter: drop-shadow(0 0 8px ${markerColor});
            "
          >
            <rect x="2" y="8" width="14" height="8" rx="1" fill="${markerColor}" stroke="white" stroke-width="0.5"/>
            <polygon points="16,8 22,12 22,16 16,16" fill="${markerColor}" stroke="white" stroke-width="0.5"/>
            <circle cx="6" cy="18" r="2" fill="#1f2937" stroke="${markerColor}" stroke-width="1"/>
            <circle cx="14" cy="18" r="2" fill="#1f2937" stroke="${markerColor}" stroke-width="1"/>
            <circle cx="20" cy="18" r="1.5" fill="#1f2937" stroke="${markerColor}" stroke-width="1"/>
            <rect x="4" y="4" width="8" height="4" rx="0.5" fill="${markerColor}" opacity="0.7"/>
          </svg>
          <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            width: 4px;
            height: 4px;
            margin: -2px;
            background: white;
            border-radius: 50%;
            box-shadow: 0 0 4px white;
          "></div>
        </div>
      `,
      iconSize: [56, 56],
      iconAnchor: [28, 28],
    });

    if (markerRef.current) {
      markerRef.current.setLatLng([currentPosition.latitude, currentPosition.longitude]);
      markerRef.current.setIcon(icon);
    } else {
      markerRef.current = L.marker([currentPosition.latitude, currentPosition.longitude], { icon })
        .addTo(mapRef.current);
    }

    // Pan to position if not in playback mode
    if (playbackIndex < 0) {
      mapRef.current.panTo([currentPosition.latitude, currentPosition.longitude], {
        animate: true,
        duration: 0.5,
      });
    }
  }, [currentPosition, playbackIndex, isUnderground]);

  // Update track polyline
  useEffect(() => {
    if (!mapRef.current) return;

    const displayPositions = playbackIndex >= 0 
      ? trackHistory.slice(0, playbackIndex + 1)
      : trackHistory;

    const coordinates = displayPositions.map(pos => [pos.latitude, pos.longitude] as [number, number]);

    // Remove existing polylines
    if (polylineRef.current) {
      mapRef.current.removeLayer(polylineRef.current);
    }
    if (glowPolylineRef.current) {
      mapRef.current.removeLayer(glowPolylineRef.current);
    }

    if (coordinates.length > 1) {
      const trackColor = isUnderground ? 'rgb(245, 158, 11)' : 'rgb(14, 184, 195)';

      // Add glow effect first
      glowPolylineRef.current = L.polyline(coordinates, {
        color: trackColor,
        weight: 10,
        opacity: 0.2,
        lineCap: 'round',
        lineJoin: 'round',
      }).addTo(mapRef.current);

      // Add main track
      polylineRef.current = L.polyline(coordinates, {
        color: trackColor,
        weight: 4,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round',
      }).addTo(mapRef.current);
    }
  }, [trackHistory, playbackIndex, isUnderground]);

  // Update geofences
  useEffect(() => {
    if (!mapRef.current) return;

    // Remove existing geofence layers
    geofenceLayersRef.current.forEach(layer => {
      mapRef.current?.removeLayer(layer);
    });
    geofenceLayersRef.current = [];

    // Add new geofences
    geofences.forEach(geofence => {
      if (!geofence.isActive || !mapRef.current) return;

      const getGeofenceColor = (zoneType: Geofence['zoneType']) => {
        switch (zoneType) {
          case 'safe': return 'rgb(34, 197, 94)';
          case 'restricted': return 'rgb(249, 115, 22)';
          case 'hazard': return 'rgb(239, 68, 68)';
          case 'emergency_point': return 'rgb(59, 130, 246)';
          default: return 'rgb(245, 158, 11)';
        }
      };

      const color = getGeofenceColor(geofence.zoneType);

      const circle = L.circle([geofence.center.lat, geofence.center.lng], {
        radius: geofence.radius,
        color,
        fillColor: color,
        fillOpacity: 0.1,
        weight: 2,
        dashArray: geofence.zoneType === 'hazard' ? '5, 5' : '10, 6',
        opacity: 0.7,
      }).addTo(mapRef.current);

      // Add label
      const labelIcon = L.divIcon({
        className: 'geofence-label',
        html: `<div style="
          background: ${color};
          color: white;
          padding: 2px 6px;
          border-radius: 3px;
          font-size: 9px;
          font-weight: bold;
          white-space: nowrap;
          opacity: 0.9;
        ">${geofence.name}</div>`,
        iconSize: [100, 20],
        iconAnchor: [50, 10],
      });

      const label = L.marker([geofence.center.lat, geofence.center.lng], { icon: labelIcon })
        .addTo(mapRef.current);

      geofenceLayersRef.current.push(circle);
      geofenceLayersRef.current.push(label as unknown as L.Circle);
    });
  }, [geofences]);

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full rounded-xl overflow-hidden"
      style={{ background: 'hsl(222 47% 4%)' }}
    />
  );
};

export default TrackingMap;