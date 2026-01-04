import { 
  Navigation, 
  Battery, 
  Gauge, 
  Signal, 
  Clock,
  MapPin,
  Compass,
  ArrowDown,
  ArrowUp,
  Layers,
  Wifi,
  Mountain
} from 'lucide-react';
import { GPSPosition, Device } from '@/types/tracking';
import { formatDistanceToNow } from 'date-fns';

interface StatusPanelProps {
  position: GPSPosition | null;
  device: Device | null;
  isUnderground?: boolean;
}

const StatusPanel = ({ position, device, isUnderground }: StatusPanelProps) => {
  const getBatteryColor = (level: number | undefined) => {
    if (!level) return 'text-muted-foreground';
    if (level > 50) return 'text-success';
    if (level > 20) return 'text-warning';
    return 'text-destructive';
  };

  const getBatteryIcon = (level: number | undefined) => {
    if (!level) return 0;
    return Math.min(100, Math.max(0, level));
  };

  const getSignalColor = (strength: number | undefined) => {
    if (!strength) return 'text-muted-foreground';
    if (strength > 70) return 'text-success';
    if (strength > 40) return 'text-warning';
    return 'text-destructive';
  };

  const getStatusColor = (status: Device['status']) => {
    switch (status) {
      case 'operational': return 'text-success';
      case 'maintenance': return 'text-warning';
      case 'breakdown': return 'text-orange-500';
      case 'emergency': return 'text-destructive';
      default: return 'text-muted-foreground';
    }
  };

  const formatCoordinate = (value: number, type: 'lat' | 'lng') => {
    const direction = type === 'lat' 
      ? (value >= 0 ? 'N' : 'S')
      : (value >= 0 ? 'E' : 'W');
    return `${Math.abs(value).toFixed(6)}° ${direction}`;
  };

  const getHeadingDirection = (heading: number) => {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(heading / 45) % 8;
    return directions[index];
  };

  return (
    <div className="glass-panel p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`status-indicator ${device?.isOnline ? 'status-online' : 'status-offline'}`} />
          <div>
            <h3 className="font-semibold text-foreground">{device?.name || 'Unknown Vehicle'}</h3>
            <p className="text-xs text-muted-foreground capitalize">
              {device?.type?.replace('_', ' ') || 'mining vehicle'}
            </p>
          </div>
        </div>
        <div className={`px-2 py-1 rounded text-xs font-bold uppercase ${getStatusColor(device?.status)}`}>
          {device?.status || 'unknown'}
        </div>
      </div>

      {/* Zone & Depth Info */}
      {isUnderground && (
        <>
          <div className="h-px bg-border/50" />
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-warning/10 border border-warning/30 rounded-lg p-3">
              <div className="flex items-center gap-2 text-warning mb-1">
                <Layers className="w-3.5 h-3.5" />
                <span className="text-xs uppercase tracking-wide">Zone</span>
              </div>
              <div className="font-mono text-sm font-semibold text-foreground truncate">
                {position?.zone || 'Unknown'}
              </div>
            </div>

            <div className="bg-warning/10 border border-warning/30 rounded-lg p-3">
              <div className="flex items-center gap-2 text-warning mb-1">
                <ArrowDown className="w-3.5 h-3.5" />
                <span className="text-xs uppercase tracking-wide">Depth</span>
              </div>
              <div className="font-mono text-xl font-semibold text-foreground">
                {position?.depth || 0}
                <span className="text-xs text-muted-foreground ml-1">m</span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Divider */}
      <div className="h-px bg-border/50" />

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        {/* Speed */}
        <div className="bg-secondary/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <Gauge className="w-3.5 h-3.5" />
            <span className="text-xs uppercase tracking-wide">Speed</span>
          </div>
          <div className="font-mono text-xl font-semibold text-foreground">
            {position?.speed?.toFixed(1) || '0.0'}
            <span className="text-xs text-muted-foreground ml-1">km/h</span>
          </div>
        </div>

        {/* Heading */}
        <div className="bg-secondary/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <Compass className="w-3.5 h-3.5" />
            <span className="text-xs uppercase tracking-wide">Heading</span>
          </div>
          <div className="font-mono text-xl font-semibold text-foreground">
            {position?.heading || 0}°
            <span className="text-xs text-muted-foreground ml-1">
              {position ? getHeadingDirection(position.heading) : 'N'}
            </span>
          </div>
        </div>

        {/* Signal Strength */}
        <div className="bg-secondary/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <Wifi className={`w-3.5 h-3.5 ${getSignalColor(position?.signalStrength)}`} />
            <span className="text-xs uppercase tracking-wide">Signal</span>
          </div>
          <div className={`font-mono text-xl font-semibold ${getSignalColor(position?.signalStrength)}`}>
            {position?.signalStrength?.toFixed(0) || '--'}
            <span className="text-xs ml-0.5">%</span>
          </div>
          <div className="mt-2 h-1 bg-muted rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                (position?.signalStrength || 0) > 70 ? 'bg-success' :
                (position?.signalStrength || 0) > 40 ? 'bg-warning' : 'bg-destructive'
              }`}
              style={{ width: `${position?.signalStrength || 0}%` }}
            />
          </div>
        </div>

        {/* Battery */}
        <div className="bg-secondary/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <Battery className={`w-3.5 h-3.5 ${getBatteryColor(position?.battery)}`} />
            <span className="text-xs uppercase tracking-wide">Battery</span>
          </div>
          <div className={`font-mono text-xl font-semibold ${getBatteryColor(position?.battery)}`}>
            {position?.battery?.toFixed(0) || '--'}
            <span className="text-xs ml-0.5">%</span>
          </div>
          <div className="mt-2 h-1 bg-muted rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                (position?.battery || 0) > 50 ? 'bg-success' :
                (position?.battery || 0) > 20 ? 'bg-warning' : 'bg-destructive'
              }`}
              style={{ width: `${getBatteryIcon(position?.battery)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Last Seen */}
      <div className="bg-secondary/50 rounded-lg p-3">
        <div className="flex items-center gap-2 text-muted-foreground mb-1">
          <Clock className="w-3.5 h-3.5" />
          <span className="text-xs uppercase tracking-wide">Last Update</span>
        </div>
        <div className="font-mono text-sm font-medium text-foreground">
          {device?.lastSeen 
            ? formatDistanceToNow(device.lastSeen, { addSuffix: true })
            : '--'
          }
        </div>
      </div>

      {/* Divider */}
      <div className="h-px bg-border/50" />

      {/* Coordinates */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <MapPin className="w-3.5 h-3.5" />
          <span className="text-xs uppercase tracking-wide">Position</span>
        </div>
        <div className="font-mono text-sm space-y-1">
          <div className="flex justify-between">
            <span className="text-muted-foreground">LAT</span>
            <span className="text-foreground">
              {position ? formatCoordinate(position.latitude, 'lat') : '--'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">LNG</span>
            <span className="text-foreground">
              {position ? formatCoordinate(position.longitude, 'lng') : '--'}
            </span>
          </div>
          {position?.accuracy && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">ACC</span>
              <span className="text-foreground">±{position.accuracy.toFixed(1)} m</span>
            </div>
          )}
          {position?.altitude !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">ALT</span>
              <span className="text-foreground">{position.altitude.toFixed(1)} m</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatusPanel;