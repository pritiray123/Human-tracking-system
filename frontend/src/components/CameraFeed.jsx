import { useEffect, useRef, useState } from 'react';
import { getActiveStreamUrl } from '../services/api';

export default function CameraFeed({
  activeDevice,
  remoteStream,
  webrtcStatus,
  webrtcStats
}) {
  const videoRef = useRef(null);
  const [actualStatus, setActualStatus] = useState('CONNECTING');
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
  const hasWebRTCStream = isRemote && Boolean(remoteStream);
  const streamUrl = getActiveStreamUrl(activeDevice.id);

  let statusLabel = 'LIVE';
  if (hasWebRTCStream) {
    statusLabel = actualStatus;
  } else if (activeDevice.status) {
    statusLabel = activeDevice.status.toUpperCase();
  }

  const statsBadgeText = webrtcStats && webrtcStats.framesDecoded > 0
    ? ` · ${webrtcStats.framesDecoded} frames`
    : '';

  return (
    <div className="camera-feed">
      {hasWebRTCStream ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="feed-video"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            background: '#000'
          }}
        />
      ) : (
        <img
          key={activeDevice.id}
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
          {activeDevice.label} {hasWebRTCStream ? ' [WebRTC]' : ''}
        </span>

        <span
          className="feed-fps"
          style={{
            color: statusLabel === 'STREAMING (P2P)' || statusLabel === 'LIVE'
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
  );
}