import { 
  AlertTriangle, 
  MapPin, 
  Battery, 
  Wifi, 
  X,
  Bell,
  Gauge
} from 'lucide-react';
import { Alert } from '@/types/tracking';
import { formatDistanceToNow } from 'date-fns';
import { Button } from '@/components/ui/button';

interface AlertsPanelProps {
  alerts: Alert[];
  onDismiss: (alertId: string) => void;
}

const AlertsPanel = ({ alerts, onDismiss }: AlertsPanelProps) => {
  const unreadAlerts = alerts.filter(a => !a.isRead);

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'geofence_enter':
      case 'geofence_exit':
        return MapPin;
      case 'low_battery':
        return Battery;
      case 'connection_lost':
        return Wifi;
      case 'speeding':
        return Gauge;
      default:
        return AlertTriangle;
    }
  };

  const getAlertColor = (type: Alert['type']) => {
    switch (type) {
      case 'geofence_exit':
        return 'text-warning border-warning/30 bg-warning/10';
      case 'geofence_enter':
        return 'text-success border-success/30 bg-success/10';
      case 'low_battery':
        return 'text-destructive border-destructive/30 bg-destructive/10';
      case 'connection_lost':
        return 'text-destructive border-destructive/30 bg-destructive/10';
      case 'speeding':
        return 'text-warning border-warning/30 bg-warning/10';
      default:
        return 'text-muted-foreground border-border bg-secondary/50';
    }
  };

  return (
    <div className="glass-panel p-4 space-y-4 max-h-80 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium">Alerts</span>
        </div>
        {unreadAlerts.length > 0 && (
          <span className="px-2 py-0.5 text-xs font-medium bg-destructive/20 text-destructive rounded-full">
            {unreadAlerts.length} new
          </span>
        )}
      </div>

      {/* Alert list */}
      <div className="flex-1 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No alerts
          </div>
        ) : (
          alerts.slice(0, 10).map(alert => {
            const Icon = getAlertIcon(alert.type);
            const colorClass = getAlertColor(alert.type);
            
            return (
              <div
                key={alert.id}
                className={`flex items-start gap-3 p-3 rounded-lg border transition-all ${colorClass} ${
                  alert.isRead ? 'opacity-50' : ''
                }`}
              >
                <Icon className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{alert.message}</p>
                  <p className="text-xs opacity-70 mt-0.5">
                    {formatDistanceToNow(alert.timestamp, { addSuffix: true })}
                  </p>
                </div>
                {!alert.isRead && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 flex-shrink-0 opacity-60 hover:opacity-100"
                    onClick={() => onDismiss(alert.id)}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default AlertsPanel;
