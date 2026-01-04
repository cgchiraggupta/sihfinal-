import { 
  Play, 
  Pause, 
  SkipBack, 
  SkipForward, 
  RotateCcw,
  Clock
} from 'lucide-react';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { GPSPosition } from '@/types/tracking';
import { format } from 'date-fns';

interface PlaybackControlsProps {
  positions: GPSPosition[];
  currentIndex: number;
  isPlaying: boolean;
  playbackSpeed: number;
  onPlay: () => void;
  onStop: () => void;
  onSeek: (index: number) => void;
  onSpeedChange: (speed: number) => void;
}

const PlaybackControls = ({
  positions,
  currentIndex,
  isPlaying,
  playbackSpeed,
  onPlay,
  onStop,
  onSeek,
  onSpeedChange,
}: PlaybackControlsProps) => {
  const currentPosition = positions[currentIndex >= 0 ? currentIndex : positions.length - 1];
  const startTime = positions[0]?.timestamp;
  const endTime = positions[positions.length - 1]?.timestamp;

  const handleSliderChange = (value: number[]) => {
    onSeek(value[0]);
  };

  const handleSkipBack = () => {
    const newIndex = Math.max(0, currentIndex - 10);
    onSeek(newIndex);
  };

  const handleSkipForward = () => {
    const newIndex = Math.min(positions.length - 1, currentIndex + 10);
    onSeek(newIndex);
  };

  const handleReset = () => {
    onStop();
    onSeek(positions.length - 1);
  };

  const speedOptions = [0.5, 1, 2, 4];

  return (
    <div className="glass-panel p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium">Track Playback</span>
        </div>
        <div className="text-xs text-muted-foreground font-mono">
          {positions.length} points
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-2">
        <Slider
          value={[currentIndex >= 0 ? currentIndex : positions.length - 1]}
          max={positions.length - 1}
          min={0}
          step={1}
          onValueChange={handleSliderChange}
          className="cursor-pointer"
        />
        
        <div className="flex justify-between text-xs font-mono text-muted-foreground">
          <span>{startTime ? format(startTime, 'HH:mm:ss') : '--:--:--'}</span>
          <span className="text-primary font-medium">
            {currentPosition?.timestamp 
              ? format(currentPosition.timestamp, 'HH:mm:ss')
              : '--:--:--'
            }
          </span>
          <span>{endTime ? format(endTime, 'HH:mm:ss') : '--:--:--'}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleSkipBack}
            disabled={!isPlaying && currentIndex <= 0}
          >
            <SkipBack className="w-4 h-4" />
          </Button>
          
          <Button
            variant="default"
            size="icon"
            className="h-10 w-10 rounded-full glow-primary"
            onClick={isPlaying ? onStop : onPlay}
          >
            {isPlaying ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5 ml-0.5" />
            )}
          </Button>
          
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleSkipForward}
            disabled={!isPlaying && currentIndex >= positions.length - 1}
          >
            <SkipForward className="w-4 h-4" />
          </Button>
          
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleReset}
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
        </div>

        {/* Speed selector */}
        <div className="flex items-center gap-1 bg-secondary/50 rounded-lg p-1">
          {speedOptions.map(speed => (
            <button
              key={speed}
              onClick={() => onSpeedChange(speed)}
              className={`px-2 py-1 text-xs font-mono rounded transition-colors ${
                playbackSpeed === speed
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>

      {/* Current stats during playback */}
      {isPlaying && currentPosition && (
        <div className="flex items-center justify-center gap-6 pt-2 border-t border-border/50 text-xs font-mono">
          <div>
            <span className="text-muted-foreground">Speed: </span>
            <span className="text-foreground">{currentPosition.speed?.toFixed(1)} km/h</span>
          </div>
          <div>
            <span className="text-muted-foreground">Heading: </span>
            <span className="text-foreground">{currentPosition.heading}°</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlaybackControls;
