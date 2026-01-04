import { useState, useMemo, useEffect } from 'react';
import { useSupabaseTracking } from '@/hooks/useSupabaseTracking';
import TrackingMap from '@/components/tracking/TrackingMap';
import MineVisualization3D from '@/components/tracking/MineVisualization3D';
import { 
  HardHat, Maximize2, Minimize2, AlertTriangle, Wifi, 
  Play, Pause, SkipBack, SkipForward, RotateCcw,
  MapPin, Clock, Battery, Compass, Gauge, Radio,
  ChevronLeft, ChevronRight, Layers, Grid3X3
} from 'lucide-react';
import { ViewMode } from '@/types/mine3d';

const Index = () => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('3d');
  const [simulationEnabled, setSimulationEnabled] = useState(false);
  const [showWireframe, setShowWireframe] = useState(true);
  const [showLevels, setShowLevels] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackIndex, setPlaybackIndex] = useState(-1);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  
  const {
    devices,
    currentDevice,
    currentPosition,
    trackHistory,
    allDevicePositions,
    allDeviceTrackHistory,
    alerts,
    geofences,
    isLoading,
    isSimulating,
    isUnderground,
    selectDevice,
    triggerEmergency,
    reportBreakdown,
    dismissAlert,
  } = useSupabaseTracking({ simulationMode: simulationEnabled });

  const isEmergencyActive = currentDevice?.status === 'emergency' || currentDevice?.status === 'breakdown';

  // Format time ago
  const lastUpdateText = useMemo(() => {
    if (!currentPosition?.timestamp) return 'No data';
    const diff = Date.now() - new Date(currentPosition.timestamp).getTime();
    if (diff < 60000) return 'less than a minute ago';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes ago`;
    return `${Math.floor(diff / 3600000)} hours ago`;
  }, [currentPosition?.timestamp]);

  // Get heading direction
  const headingDirection = useMemo(() => {
    const heading = currentPosition?.heading || 0;
    if (heading >= 337.5 || heading < 22.5) return 'N';
    if (heading >= 22.5 && heading < 67.5) return 'NE';
    if (heading >= 67.5 && heading < 112.5) return 'E';
    if (heading >= 112.5 && heading < 157.5) return 'SE';
    if (heading >= 157.5 && heading < 202.5) return 'S';
    if (heading >= 202.5 && heading < 247.5) return 'SW';
    if (heading >= 247.5 && heading < 292.5) return 'W';
    return 'NW';
  }, [currentPosition?.heading]);

  // Playback handlers
  const handleTogglePlay = () => {
    if (!isPlaying && playbackIndex < 0 && trackHistory.length > 0) {
      setPlaybackIndex(0); // Start from beginning
    }
    setIsPlaying(!isPlaying);
  };
  const handleStop = () => {
    setIsPlaying(false);
    setPlaybackIndex(-1);
  };
  const handleSkipBack = () => {
    if (trackHistory.length === 0) return;
    setPlaybackIndex(prev => Math.max(0, prev - 1));
    setIsPlaying(false);
  };
  const handleSkipForward = () => {
    if (trackHistory.length === 0) return;
    setPlaybackIndex(prev => Math.min(trackHistory.length - 1, prev + 1));
    setIsPlaying(false);
  };

  // Playback advancement
  useEffect(() => {
    if (!isPlaying || trackHistory.length === 0) return;

    // Initialize playback index if needed
    if (playbackIndex < 0) {
      setPlaybackIndex(0);
      return;
    }

    const interval = setInterval(() => {
      setPlaybackIndex(prev => {
        const next = prev + playbackSpeed;
        if (next >= trackHistory.length) {
          setIsPlaying(false);
          return trackHistory.length - 1;
        }
        return Math.floor(next);
      });
    }, 1000 / playbackSpeed); // Adjust speed

    return () => clearInterval(interval);
  }, [isPlaying, trackHistory.length, playbackSpeed, playbackIndex]);

  // Toggle simulation
  const handleToggleSimulation = () => {
    setSimulationEnabled(!simulationEnabled);
  };

  // Get depth color
  const getDepthColor = (depth: number) => {
    if (depth <= 0) return '#22c55e';
    if (depth <= 50) return '#0ea5e9';
    if (depth <= 100) return '#a855f7';
    if (depth <= 150) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] text-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#0d1219]/95 backdrop-blur-sm border-b border-cyan-900/30">
        <div className="flex items-center justify-between px-4 py-2">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/20 flex items-center justify-center">
              <HardHat className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-white">Mining Intelligence</h1>
              <p className="text-[10px] text-gray-500">Underground Vehicle Tracking System</p>
            </div>
          </div>
          
          {/* Right Controls */}
          <div className="flex items-center gap-3">
            {/* Status Indicator */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${
              isUnderground 
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' 
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isUnderground ? 'bg-amber-400' : 'bg-emerald-400'}`} />
              <span className="text-xs font-medium">{isUnderground ? 'UNDERGROUND' : 'SURFACE'}</span>
              </div>

            {/* Signal */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30">
              <Wifi className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-xs font-medium text-cyan-400">{currentPosition?.signalStrength || 0}%</span>
              </div>

            {/* 2D/3D Toggle */}
            <div className="flex items-center bg-[#1a2332] rounded-lg p-0.5">
              <button
                onClick={() => setViewMode('2d')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  viewMode === '2d'
                    ? 'bg-cyan-500 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <Grid3X3 className="w-3.5 h-3.5" />
                2D
              </button>
              <button
                onClick={() => setViewMode('3d')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  viewMode === '3d'
                    ? 'bg-cyan-500 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                3D
              </button>
            </div>
            
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 rounded-lg bg-[#1a2332] text-gray-400 hover:text-white transition-colors"
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-14 h-screen flex">
        {/* Left Sidebar - View Options */}
        <aside className="w-56 p-4 border-r border-cyan-900/30 bg-[#0d1219]/50 overflow-y-auto flex-shrink-0">
          {/* View Options */}
          <div className="mb-6">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">View Options</h3>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setShowWireframe(!showWireframe)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${
                  showWireframe
                    ? 'bg-cyan-500 text-white'
                    : 'bg-[#1a2332] text-gray-400 hover:text-white'
                }`}
              >
                <span>🔲</span>
                Wireframe
              </button>
              <button
                onClick={() => setShowLevels(!showLevels)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${
                  showLevels
                    ? 'bg-cyan-500 text-white'
                    : 'bg-[#1a2332] text-gray-400 hover:text-white'
                }`}
              >
                <span>📊</span>
                Levels
              </button>
            </div>
          </div>

          {/* Device Selector */}
          <div className="mb-6">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">🚜 Vehicles</h3>
            <div className="space-y-1">
              {devices.map((device) => (
                <button
                  key={device.id}
                  onClick={() => selectDevice(device.id)}
                  className={`w-full px-3 py-2 rounded-lg text-left text-xs transition-all ${
                    currentDevice?.id === device.id
                      ? 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-400'
                      : 'bg-[#1a2332] text-gray-400 hover:text-white border border-transparent'
                  }`}
                >
          <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${device.is_online ? 'bg-emerald-400' : 'bg-gray-600'}`} />
                    <span className="truncate">{device.name}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Simulation Toggle */}
          <div className="mb-6">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Simulation</h3>
            <button
              onClick={handleToggleSimulation}
              className={`w-full px-3 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wide transition-all flex items-center justify-center gap-2 ${
                simulationEnabled
                  ? 'bg-gradient-to-r from-emerald-600 to-emerald-500 text-white shadow-lg shadow-emerald-500/20 border border-emerald-400/30'
                  : 'bg-[#1a2332] text-gray-400 hover:text-white border border-gray-700 hover:border-cyan-500/50'
              }`}
            >
              {simulationEnabled ? (
                <>
                  <div className="relative">
                    <div className="w-2 h-2 rounded-full bg-white animate-ping absolute" />
                    <div className="w-2 h-2 rounded-full bg-white relative" />
                  </div>
                  <span>Live</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 rounded-full bg-gray-500" />
                  <span>Start Sim</span>
                </>
              )}
            </button>
          </div>

          {/* Workstations */}
          <div className="mb-6">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">🏭 Workstations</h3>
            <div className="space-y-1">
              {[
                { id: 'ws1', name: 'Main Shaft Entry', level: 'Surface', status: 'active' },
                { id: 'ws2', name: 'Level 1 Station', level: '-50m', status: 'active' },
                { id: 'ws3', name: 'Workshop', level: '-50m', status: 'active' },
                { id: 'ws4', name: 'Level 2 Station', level: '-150m', status: 'active' },
                { id: 'ws5', name: 'Face A', level: '-150m', status: 'warning' },
                { id: 'ws6', name: 'Face B', level: '-150m', status: 'active' },
                { id: 'ws7', name: 'Level 3 Station', level: '-250m', status: 'inactive' },
                { id: 'ws8', name: 'Extraction Point', level: '-260m', status: 'inactive' },
              ].map((ws) => (
                <button
                  key={ws.id}
                  className="w-full px-2 py-1.5 rounded-lg text-left text-[11px] transition-all bg-[#1a2332]/50 hover:bg-[#1a2332] border border-transparent hover:border-cyan-500/30"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${
                        ws.status === 'active' ? 'bg-emerald-400' :
                        ws.status === 'warning' ? 'bg-amber-400' : 'bg-gray-600'
                      }`} />
                      <span className="text-gray-300 truncate">{ws.name}</span>
                    </div>
                    <span className="text-gray-500 text-[10px]">{ws.level}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Tunnel Types Legend */}
          <div>
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Tunnel Types</h3>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-amber-400 rounded" />
                <span className="text-gray-400">Main Decline</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-cyan-400 rounded" />
                <span className="text-gray-400">Level Drive</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-orange-400 rounded" />
                <span className="text-gray-400">Extraction</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-emerald-400 rounded" />
                <span className="text-gray-400">Emergency</span>
              </div>
            </div>
        </div>
        </aside>

        {/* Main Visualization Area */}
        <div className="flex-1 flex flex-col relative">
          {/* 3D/2D View */}
          <div className="flex-1 relative">
            {viewMode === '2d' ? (
              <TrackingMap
                currentPosition={currentPosition}
                trackHistory={trackHistory}
                geofences={geofences}
                playbackIndex={playbackIndex}
                mineZones={[]}
                isUnderground={isUnderground}
              />
            ) : (
              <MineVisualization3D
                currentPosition={currentPosition}
                trackHistory={trackHistory}
                device={currentDevice}
                devices={devices.map(d => ({
                  id: d.id,
                  name: d.name,
                  type: d.type as 'mining_vehicle' | 'personnel' | 'equipment',
                  lastPosition: null,
                  isOnline: d.is_online,
                  lastSeen: d.last_seen_at ? new Date(d.last_seen_at) : new Date(),
                  status: d.status as 'operational' | 'breakdown' | 'maintenance' | 'emergency'
                }))}
                allDevicePositions={allDevicePositions}
                allDeviceTrackHistory={allDeviceTrackHistory}
                isUnderground={isUnderground}
                showWireframe={showWireframe}
                showLevels={showLevels}
                playbackIndex={playbackIndex}
              />
            )}

            {/* Vehicle Info Overlay - Top Left */}
            {currentDevice && (
              <div className="absolute top-4 right-4 bg-[#0d1219]/90 backdrop-blur-sm border border-cyan-500/30 rounded-xl p-4 min-w-[200px]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-cyan-400 font-bold text-sm">{currentDevice.name}</span>
                </div>
                <div className="space-y-1 text-xs text-gray-400">
                  <div className="flex justify-between">
                    <span>Depth:</span>
                    <span className="text-white font-mono">{Math.abs(currentPosition?.depth || 0).toFixed(0)}m</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Zone:</span>
                    <span className="text-white font-mono">{currentPosition?.zone || 'Surface'}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Depth Legend - Bottom Right of 3D View */}
            {viewMode === '3d' && (
              <div className="absolute bottom-24 right-4 bg-[#0d1219]/90 backdrop-blur-sm border border-cyan-500/30 rounded-xl p-3">
                <h4 className="text-[10px] font-semibold text-gray-500 uppercase mb-2">Depth</h4>
                <div className="space-y-1.5 text-xs">
                  {[
                    { depth: '0m', color: '#22c55e' },
                    { depth: '-50m', color: '#0ea5e9' },
                    { depth: '-100m', color: '#a855f7' },
                    { depth: '-150m', color: '#f59e0b' },
                    { depth: '-200m', color: '#ef4444' },
                  ].map(item => (
                    <div key={item.depth} className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-gray-400 font-mono">{item.depth}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Controls Hint */}
            <div className="absolute bottom-24 left-4 text-[10px] text-gray-500 space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 border border-gray-600 rounded flex items-center justify-center text-[8px]">◻</div>
                <span>Drag to rotate</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="w-3 h-3 text-gray-600" />
                <span>Scroll to zoom</span>
              </div>
            </div>
          </div>
          
          {/* Bottom Controls Bar */}
          <div className="h-20 bg-[#0d1219] border-t border-cyan-900/30 px-4 flex items-center justify-between">
            {/* Playback Controls */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                <span className="text-sm font-medium text-white">Track Playback</span>
                <span className="text-xs text-gray-500">{trackHistory.length} points</span>
              </div>
              
              {/* Timeline */}
              <div className="w-64">
                <div className="relative h-1 bg-[#1a2332] rounded-full">
                  <div 
                    className="absolute h-full bg-cyan-500 rounded-full transition-all"
                    style={{ 
                      width: trackHistory.length > 0 && playbackIndex >= 0 
                        ? `${((playbackIndex + 1) / trackHistory.length) * 100}%` 
                        : trackHistory.length > 0 && currentPosition
                        ? '100%'
                        : '0%' 
                    }}
                  />
                  <div 
                    className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-cyan-400 rounded-full border-2 border-[#0d1219] transition-all"
                    style={{ 
                      left: trackHistory.length > 0 && playbackIndex >= 0
                        ? `${((playbackIndex + 1) / trackHistory.length) * 100}%`
                        : trackHistory.length > 0 && currentPosition
                        ? '100%'
                        : '0%',
                      transform: 'translate(-50%, -50%)'
                    }}
                  />
                </div>
                <div className="flex justify-between mt-1 text-[10px] text-gray-500 font-mono">
                  <span>{trackHistory[0]?.timestamp ? new Date(trackHistory[0].timestamp).toLocaleTimeString() : '--:--:--'}</span>
                  <span className="text-cyan-400">
                    {playbackIndex >= 0 && trackHistory[playbackIndex]?.timestamp 
                      ? new Date(trackHistory[playbackIndex].timestamp).toLocaleTimeString() 
                      : currentPosition?.timestamp 
                        ? new Date(currentPosition.timestamp).toLocaleTimeString() 
                        : '--:--:--'}
                  </span>
                  <span>{trackHistory[trackHistory.length - 1]?.timestamp ? new Date(trackHistory[trackHistory.length - 1].timestamp).toLocaleTimeString() : '--:--:--'}</span>
                </div>
              </div>

              {/* Play Controls */}
              <div className="flex items-center gap-1">
                <button 
                  onClick={handleSkipBack}
                  disabled={trackHistory.length === 0 || playbackIndex <= 0}
                  className="p-1.5 rounded-lg bg-[#1a2332] text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <SkipBack className="w-4 h-4" />
                </button>
                <button 
                  onClick={handleTogglePlay}
                  disabled={trackHistory.length === 0}
                  className="p-2 rounded-lg bg-cyan-500 text-white hover:bg-cyan-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>
                <button 
                  onClick={handleSkipForward}
                  disabled={trackHistory.length === 0 || playbackIndex >= trackHistory.length - 1}
                  className="p-1.5 rounded-lg bg-[#1a2332] text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <SkipForward className="w-4 h-4" />
                </button>
                <button 
                  onClick={handleStop} 
                  disabled={trackHistory.length === 0}
                  className="p-1.5 rounded-lg bg-[#1a2332] text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              </div>

              {/* Speed Controls */}
              <div className="flex items-center gap-1">
                {[0.5, 1, 2, 4].map(speed => (
                  <button
                    key={speed}
                    onClick={() => setPlaybackSpeed(speed)}
                    className={`px-2 py-1 rounded text-xs font-medium transition-all ${
                      playbackSpeed === speed
                        ? 'bg-[#1a2332] text-white border border-cyan-500/50'
                        : 'text-gray-500 hover:text-white'
                    }`}
                  >
                    {speed}x
                  </button>
                ))}
              </div>
            </div>

            {/* Emergency Buttons */}
            <div className="flex items-center gap-3">
              <button
                onClick={triggerEmergency}
                disabled={!currentPosition}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/20 border border-red-500 text-red-400 hover:bg-red-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <AlertTriangle className="w-4 h-4" />
                <span className="text-sm font-semibold">EMERGENCY</span>
              </button>
              <button
                onClick={reportBreakdown}
                disabled={!currentPosition}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500/20 border border-amber-500 text-amber-400 hover:bg-amber-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Gauge className="w-4 h-4" />
                <span className="text-sm font-semibold">BREAKDOWN</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Sidebar - Status Panel */}
        <aside className={`w-72 border-l border-cyan-900/30 bg-[#0d1219]/50 overflow-y-auto transition-all ${isFullscreen ? 'hidden' : ''}`}>
          <div className="p-4 space-y-4">
            {/* Vehicle Status Card */}
            <div className="bg-[#1a2332]/50 rounded-xl p-4 border border-cyan-900/30">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className={`w-2.5 h-2.5 rounded-full ${
                    currentDevice?.status === 'operational' ? 'bg-emerald-400' :
                    currentDevice?.status === 'emergency' ? 'bg-red-400 animate-pulse' :
                    currentDevice?.status === 'breakdown' ? 'bg-amber-400' : 'bg-gray-400'
                  }`} />
                  <div>
                    <h3 className="text-sm font-semibold text-white">{currentDevice?.name || 'No Vehicle'}</h3>
                    <p className="text-[10px] text-gray-500">{currentDevice?.type || 'Unknown'}</p>
                  </div>
                </div>
                <span className={`text-[10px] font-bold uppercase ${
                  currentDevice?.status === 'operational' ? 'text-emerald-400' :
                  currentDevice?.status === 'emergency' ? 'text-red-400' :
                  currentDevice?.status === 'breakdown' ? 'text-amber-400' : 'text-gray-400'
                }`}>
                  {currentDevice?.status || 'OFFLINE'}
                </span>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-3">
                {/* Speed */}
                <div className="bg-[#0d1219] rounded-lg p-3">
                  <div className="flex items-center gap-1.5 text-gray-500 mb-1">
                    <Gauge className="w-3 h-3" />
                    <span className="text-[10px] uppercase">Speed</span>
                  </div>
                  <div className="text-lg font-bold text-white">
                    {(currentPosition?.speed || 0).toFixed(1)}
                    <span className="text-xs text-gray-500 ml-1">km/h</span>
                  </div>
                </div>

                {/* Heading */}
                <div className="bg-[#0d1219] rounded-lg p-3">
                  <div className="flex items-center gap-1.5 text-gray-500 mb-1">
                    <Compass className="w-3 h-3" />
                    <span className="text-[10px] uppercase">Heading</span>
                  </div>
                  <div className="text-lg font-bold text-white">
                    {Math.round(currentPosition?.heading || 0)}°
                    <span className="text-xs text-gray-500 ml-1">{headingDirection}</span>
                  </div>
                </div>

                {/* Signal */}
                <div className="bg-[#0d1219] rounded-lg p-3">
                  <div className="flex items-center gap-1.5 text-gray-500 mb-1">
                    <Wifi className="w-3 h-3" />
                    <span className="text-[10px] uppercase">Signal</span>
                  </div>
                  <div className="text-lg font-bold" style={{ color: (currentPosition?.signalStrength || 0) > 50 ? '#22c55e' : '#f59e0b' }}>
                    {currentPosition?.signalStrength || 0}%
                  </div>
                  <div className="mt-1 h-1 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full rounded-full transition-all"
                      style={{ 
                        width: `${currentPosition?.signalStrength || 0}%`,
                        backgroundColor: (currentPosition?.signalStrength || 0) > 50 ? '#22c55e' : '#f59e0b'
                      }}
                    />
                  </div>
                </div>

                {/* Battery */}
                <div className="bg-[#0d1219] rounded-lg p-3">
                  <div className="flex items-center gap-1.5 text-gray-500 mb-1">
                    <Battery className="w-3 h-3" />
                    <span className="text-[10px] uppercase">Battery</span>
                  </div>
                  <div className="text-lg font-bold text-emerald-400">
                    {currentPosition?.battery || 85}%
                  </div>
                  <div className="mt-1 h-1 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-emerald-400 rounded-full transition-all"
                      style={{ width: `${currentPosition?.battery || 85}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Last Update */}
            <div className="bg-[#1a2332]/50 rounded-xl p-4 border border-cyan-900/30">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <Clock className="w-3 h-3" />
                <span className="text-[10px] uppercase">Last Update</span>
              </div>
              <p className="text-sm text-white">{lastUpdateText}</p>
            </div>

            {/* Position Details */}
            <div className="bg-[#1a2332]/50 rounded-xl p-4 border border-cyan-900/30">
              <div className="flex items-center gap-2 text-gray-500 mb-3">
                <MapPin className="w-3 h-3" />
                <span className="text-[10px] uppercase">Position</span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-500">LAT</span>
                  <span className="text-white font-mono">{currentPosition?.latitude?.toFixed(6) || '0.000000'}° N</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">LNG</span>
                  <span className="text-white font-mono">{currentPosition?.longitude?.toFixed(6) || '0.000000'}° E</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">ACC</span>
                  <span className="text-white font-mono">±{currentPosition?.accuracy?.toFixed(1) || '0.0'} m</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">ALT</span>
                  <span className="text-white font-mono">{(currentPosition?.altitude || 0).toFixed(1)} m</span>
                </div>
              </div>
            </div>

            {/* Alerts */}
            <div className="bg-[#1a2332]/50 rounded-xl p-4 border border-cyan-900/30">
              <div className="flex items-center gap-2 text-gray-500 mb-3">
                <AlertTriangle className="w-3 h-3" />
                <span className="text-[10px] uppercase">Alerts</span>
              </div>
              {alerts.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-2">No alerts</p>
              ) : (
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {alerts.slice(0, 5).map(alert => (
                    <div 
                      key={alert.id}
                      className={`p-2 rounded-lg text-xs ${
                        alert.priority === 'critical' ? 'bg-red-500/20 border border-red-500/50' :
                        alert.priority === 'high' ? 'bg-amber-500/20 border border-amber-500/50' :
                        'bg-cyan-500/10 border border-cyan-500/30'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className={
                          alert.priority === 'critical' ? 'text-red-400' :
                          alert.priority === 'high' ? 'text-amber-400' : 'text-cyan-400'
                        }>
                          {alert.message}
                        </span>
                        <button 
                          onClick={() => dismissAlert(alert.id)}
                          className="text-gray-500 hover:text-white"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
};

export default Index;
