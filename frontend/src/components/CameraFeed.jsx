import { useEffect, useRef, useState } from 'react';
import { getActiveStreamUrl, controlDeviceVideo, setDeviceTracking } from '../services/api';

export default function CameraFeed({
  activeDevice,
  remoteStream,
  webrtcStatus,
  webrtcStats,
  onToggleTracking
}) {
  const videoRef = useRef(null);
  const [actualStatus, setActualStatus] = useState('CONNECTING');
  const [isLooping, setIsLooping] = useState(true);
  const [togglingTracking, setTogglingTracking] = useState(false);
  const lastTimeRef = useRef(0);
  const stallCountRef = useRef(0);

  useEffect(() => {
    if (videoRef.current && remoteStream) {
      if (videoRef.current.srcObject !== remoteStream) {
        console.log('[HTS Feed] Attaching WebRTC MediaStream to video element');
        videoRef.current.srcObject = remoteStream;
        videoRef.current.play().catch(e => console.warn('[HTS Feed] Video play catch:', e));
      }
    }
  }, [remoteStream]);

  useEffect(() => {
    let interval = null;

    interval = setInterval(() => {
      const v = videoRef.current;
      if (!v || !remoteStream) {
        setActualStatus(webrtcStatus || 'DISCONNECTED');
        return;
      }

      const hasVideoBounds = v.videoWidth > 0 && v.videoHeight > 0;
      const isAdvancing = v.currentTime > lastTimeRef.current;
      const isReady = v.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA;

      if (hasVideoBounds && isAdvancing && isReady) {
        lastTimeRef.current = v.currentTime;
        stallCountRef.current = 0;
        setActualStatus('STREAMING (P2P)');
      } else if (hasVideoBounds && !isAdvancing) {
        stallCountRef.current += 1;
        if (stallCountRef.current >= 6) {
          setActualStatus('STALLED');
        }
      } else if (!hasVideoBounds) {
        setActualStatus('ICE CONNECTING (WAITING FOR VIDEO)');
      }
    }, 500);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [remoteStream, webrtcStatus]);

  const handleControl = async (action, extraParams = {}) => {
    if (!activeDevice) return;
    try {
      console.log(`[HTS Feed] Controlling video '${action}' for device:`, activeDevice.id);
      await controlDeviceVideo(activeDevice.id, action, extraParams);
    } catch (e) {
      console.warn('[HTS Feed] Control device video catch:', e);
    }
  };

  const toggleLoop = () => {
    const nextVal = !isLooping;
    setIsLooping(nextVal);
    handleControl('loop', { loop: nextVal });
  };

  const handleToggleTracking = async () => {
    if (!activeDevice || togglingTracking) return;
    const previousState = Boolean(activeDevice.tracking_enabled);
    const targetState = !previousState;
    setTogglingTracking(true);
    try {
      console.log(`[HTS Feed] Toggling tracking to ${targetState} for device:`, activeDevice.id);
      const result = await setDeviceTracking(activeDevice.id, targetState);
      if (!result || result.success !== true) {
        throw new Error(result?.detail || 'Tracking toggle request failed on backend');
      }
      const updatedEnabled = Boolean(result.tracking_enabled);
      onToggleTracking?.(activeDevice.id, updatedEnabled);
    } catch (e) {
      console.error('Tracking toggle failed', e);
      onToggleTracking?.(activeDevice.id, previousState);
    } finally {
      setTogglingTracking(false);
    }
  };

  if (!activeDevice) {
    return (
      <div className="camera-feed">
        <div className="feed-placeholder">
          <span className="placeholder-icon">📷</span>
          <p>No camera active</p>
          <p className="placeholder-hint">
            Select a device from the panel →
          </p>
        </div>
      </div>
    );
  }

  const isRemote = activeDevice.type === 'remote' || !activeDevice.id.startsWith('local:');
  const isVideoSource = activeDevice.source_type === 'video';
  const hasWebRTCStream = isRemote && Boolean(remoteStream);
  const isTrackingOn = Boolean(activeDevice.tracking_enabled);
  const streamUrl = getActiveStreamUrl(activeDevice.id);

  // Show direct WebRTC <video> ONLY when tracking is OFF for remote phone.
  // When tracking is ON, switch visible display element to backend MJPEG feed (img).
  const showWebRTCDisplay = hasWebRTCStream && !isTrackingOn;

  let statusLabel = 'LIVE';
  if (showWebRTCDisplay) {
    statusLabel = actualStatus;
  } else if (isTrackingOn) {
    statusLabel = 'AI TRACKING ON';
  } else if (activeDevice.status) {
    statusLabel = activeDevice.status.toUpperCase();
  }

  const statsBadgeText = webrtcStats && webrtcStats.framesDecoded > 0 && showWebRTCDisplay
    ? ` · ${webrtcStats.framesDecoded} frames`
    : '';

  return (
    <div className="camera-feed" style={{ position: 'relative' }}>
      {/* Hidden WebRTC video element to preserve WebRTC P2P connection in background when tracking is ON */}
      {hasWebRTCStream && (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="feed-video"
          style={{
            display: showWebRTCDisplay ? 'block' : 'none',
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            background: '#000'
          }}
        />
      )}

      {(!hasWebRTCStream || isTrackingOn) && (
        <img
          key={activeDevice.id + (isTrackingOn ? '-tracked' : '-raw')}
          src={streamUrl}
          alt={`${activeDevice.label} live feed`}
          className="feed-image"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain'
          }}
        />
      )}

      <div className="feed-overlay">
        <span className="feed-label">
          {activeDevice.label} {showWebRTCDisplay ? ' [WebRTC]' : isTrackingOn ? ' [AI Tracked]' : ''}
        </span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={handleToggleTracking}
            disabled={togglingTracking}
            style={{
              background: isTrackingOn ? '#00c896' : '#2a2a45',
              color: isTrackingOn ? '#000' : '#e0e0e0',
              border: isTrackingOn ? '1px solid #00c896' : '1px solid #444466',
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              boxShadow: isTrackingOn ? '0 0 10px rgba(0, 200, 150, 0.4)' : 'none',
              transition: 'all 0.2s ease'
            }}
          >
            🤖 Human Tracking: <strong>{isTrackingOn ? 'ON' : 'OFF'}</strong>
          </button>

          <span
            className="feed-fps"
            style={{
              color: isTrackingOn
                ? '#00c896'
                : (statusLabel === 'STREAMING (P2P)' || statusLabel === 'LIVE' || statusLabel === 'PLAYING')
                  ? '#00c896'
                  : statusLabel === 'STALLED'
                    ? '#e05050'
                    : '#ffaa00'
            }}
          >
            {statusLabel}{statsBadgeText}
          </span>
        </div>
      </div>

      {isVideoSource && (
        <div
          className="video-controls-bar"
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(15, 15, 26, 0.85)',
            border: '1px solid #2a2a45',
            backdropFilter: 'blur(8px)',
            borderRadius: '10px',
            padding: '8px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            zIndex: 10
          }}
        >
          <button
            onClick={() => handleControl('play')}
            style={{
              background: '#00c896',
              color: '#000',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 12px',
              fontWeight: 700,
              fontSize: '0.78rem',
              cursor: 'pointer'
            }}
          >
            ▶ Play
          </button>

          <button
            onClick={() => handleControl('pause')}
            style={{
              background: '#2a2a45',
              color: '#e0e0e0',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 12px',
              fontWeight: 600,
              fontSize: '0.78rem',
              cursor: 'pointer'
            }}
          >
            ⏸ Pause
          </button>

          <button
            onClick={() => handleControl('stop')}
            style={{
              background: '#e05050',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 12px',
              fontWeight: 600,
              fontSize: '0.78rem',
              cursor: 'pointer'
            }}
          >
            ⏹ Stop
          </button>

          <button
            onClick={() => handleControl('restart')}
            style={{
              background: '#2a2a45',
              color: '#e0e0e0',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 12px',
              fontWeight: 600,
              fontSize: '0.78rem',
              cursor: 'pointer'
            }}
          >
            ↻ Restart
          </button>

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.78rem',
              color: '#e0e0e0',
              cursor: 'pointer',
              marginLeft: '4px'
            }}
          >
            <input
              type="checkbox"
              checked={isLooping}
              onChange={toggleLoop}
            />
            🔁 Loop
          </label>
        </div>
      )}
    </div>
  );
}