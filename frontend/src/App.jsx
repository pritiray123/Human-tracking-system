import { useState, useEffect, useRef } from 'react';
import CameraFeed from './components/CameraFeed';
import DevicePanel from './components/DevicePanel';
import StatusBar from './components/StatusBar';
import { getSystemInfo, setActiveDevice as apiSetActiveDevice, disconnectDevice as apiDisconnectDevice } from './services/api';

export default function App() {
  const [devices, setDevices] = useState([]);
  const [activeDeviceId, setActiveDeviceId] = useState('');
  const [remoteStream, setRemoteStream] = useState(null);
  const [webrtcStatus, setWebrtcStatus] = useState('DISCONNECTED');
  const [webrtcStats, setWebrtcStats] = useState({ framesDecoded: 0, framesDropped: 0, jitter: 0, bytesReceived: 0 });
  const [sessionId, setSessionId] = useState('');

  const pcRef = useRef(null);
  const wsRef = useRef(null);
  const rtcIdRef = useRef('');
  const iceServersRef = useRef([
    { urls: ['stun:stun.l.google.com:19302', 'stun:stun1.l.google.com:19302'] },
    { urls: ['turn:openrelay.metered.ca:80', 'turn:openrelay.metered.ca:443'], username: 'openrelayproject', credential: 'openrelayproject' }
  ]);
  const iceTimeoutTimerRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    let statsInterval = null;

    async function initSystem() {
      try {
        const info = await getSystemInfo();
        if (!mounted) return;
        setSessionId(info.session_id || '');
        if (info.ice_servers && Array.isArray(info.ice_servers)) {
          iceServersRef.current = info.ice_servers;
        }
        connectSignalingWS(info.session_id);
      } catch (e) {
        console.error('[HTS Dashboard] System info init error:', e);
      }
    }

    function connectSignalingWS(currentSession) {
      if (!currentSession) return;
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/signaling`;

      console.log('[HTS Dashboard] Connecting WebSocket signaling:', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[HTS Dashboard] Signaling connected for session:', currentSession);
        setWebrtcStatus('SIGNALING');
        ws.send(JSON.stringify({
          type: 'join',
          sessionId: currentSession,
          role: 'viewer'
        }));
      };

      ws.onmessage = async (event) => {
        try {
          const msg = JSON.parse(event.data);

          if (msg.type === 'peer-joined' && msg.role === 'streamer') {
            console.log('[HTS Dashboard] Streamer peer joined session:', msg.deviceId);
            startWebRTCOffer(msg.deviceId, currentSession);
          } else if (msg.type === 'answer' && msg.sdp) {
            console.log(`[HTS RTC ${rtcIdRef.current}] Received SDP answer from streamer`);
            if (pcRef.current) {
              await pcRef.current.setRemoteDescription(new RTCSessionDescription({
                type: 'answer',
                sdp: msg.sdp
              }));
            }
          } else if ((msg.type === 'candidate' || msg.type === 'ice-candidate') && msg.candidate) {
            if (pcRef.current && pcRef.current.remoteDescription) {
              try {
                await pcRef.current.addIceCandidate(new RTCIceCandidate(msg.candidate));
              } catch (e) {
                console.warn(`[HTS RTC ${rtcIdRef.current}] Add ICE candidate warning:`, e);
              }
            }
          } else if (msg.type === 'peer-left') {
            console.log('[HTS Dashboard] Streamer peer left session:', msg.deviceId);
            closePeerConnection('peer-left');
            setRemoteStream(null);
            setWebrtcStatus('DISCONNECTED');
            setDevices(prev => prev.filter(d => d.id !== msg.deviceId));
            if (activeDeviceId === msg.deviceId) {
              setActiveDeviceId('');
            }
          }
        } catch (e) {
          console.warn('[HTS Dashboard] Signaling message parse warning:', e);
        }
      };

      ws.onerror = (err) => {
        console.warn('[HTS Dashboard] WebSocket error:', err);
      };

      ws.onclose = () => {
        console.log('[HTS Dashboard] WebSocket signaling closed');
      };
    }

    async function startWebRTCOffer(streamerDeviceId, currentSession) {
      if (pcRef.current && (pcRef.current.connectionState === 'connected' || pcRef.current.connectionState === 'connecting')) {
        console.log(`[HTS RTC ${rtcIdRef.current}] Skipping offer creation; existing peer connection is active in state: ${pcRef.current.connectionState}`);
        return;
      }

      closePeerConnection('starting new offer');
      const rtcId = Math.random().toString(36).substring(2, 8);
      rtcIdRef.current = rtcId;
      setWebrtcStatus('ICE CONNECTING');

      if (iceTimeoutTimerRef.current) clearTimeout(iceTimeoutTimerRef.current);
      iceTimeoutTimerRef.current = setTimeout(() => {
        if (!pcRef.current || (pcRef.current.iceConnectionState !== 'connected' && pcRef.current.iceConnectionState !== 'completed')) {
          console.warn(`[HTS RTC ${rtcId}] ICE connection timeout (5s). Closing WebRTC and falling back to JPEG stream.`);
          closePeerConnection('ICE timeout');
          setRemoteStream(null);
          setWebrtcStatus('FALLBACK STREAMING');
        }
      }, 5000);

      try {
        console.log(`[HTS RTC ${rtcId}] Creating UDP RTCPeerConnection as OFFERER with ICE servers:`, iceServersRef.current);
        const pc = new RTCPeerConnection({
          iceServers: iceServersRef.current,
          iceCandidatePoolSize: 10,
          bundlePolicy: 'max-bundle',
          rtcpMuxPolicy: 'require'
        });
        pcRef.current = pc;

        pc.ontrack = (event) => {
          console.log(`[HTS RTC ${rtcId}] Remote UDP MediaStream track received:`, event.streams);
          if (event.streams && event.streams[0]) {
            setRemoteStream(event.streams[0]);
          }
        };

        pc.onicecandidate = (event) => {
          if (event.candidate && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            console.log(`[HTS RTC ${rtcId}] Sending UDP ICE candidate type:`, event.candidate.type || 'unknown');
            wsRef.current.send(JSON.stringify({
              type: 'candidate',
              candidate: event.candidate,
              sessionId: currentSession,
              deviceId: streamerDeviceId
            }));
          }
        };

        pc.oniceconnectionstatechange = () => {
          console.log(`[HTS RTC ${rtcId}] UDP ICE connection state changed to: ${pc.iceConnectionState}`);
          if (pc.iceConnectionState === 'connected' || pc.iceConnectionState === 'completed') {
            if (iceTimeoutTimerRef.current) {
              clearTimeout(iceTimeoutTimerRef.current);
              iceTimeoutTimerRef.current = null;
            }
            console.log(`[HTS RTC ${rtcId}] WebRTC UDP P2P Connection established!`);
            setWebrtcStatus('STREAMING (P2P UDP)');
          } else if (pc.iceConnectionState === 'failed' || pc.iceConnectionState === 'disconnected') {
            console.warn(`[HTS RTC ${rtcId}] WebRTC UDP ICE failed/disconnected. Transitioning to FALLBACK STREAMING.`);
            closePeerConnection('ICE failed');
            setRemoteStream(null);
            setWebrtcStatus('FALLBACK STREAMING');
          }
        };

        console.log(`[HTS RTC ${rtcId}] Creating SDP offer…`);
        const offer = await pc.createOffer({ offerToReceiveVideo: true, offerToReceiveAudio: false });
        await pc.setLocalDescription(offer);

        console.log(`[HTS RTC ${rtcId}] Sending SDP offer to streamer device:`, streamerDeviceId);
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'offer',
            sdp: offer.sdp,
            sessionId: currentSession,
            deviceId: streamerDeviceId
          }));
        }
      } catch (err) {
        console.error(`[HTS RTC ${rtcIdRef.current}] Error creating WebRTC UDP offer:`, err);
        closePeerConnection('offer error');
        setRemoteStream(null);
        setWebrtcStatus('FALLBACK STREAMING');
      }
    }

    function closePeerConnection(reason = 'manual cleanup') {
      if (iceTimeoutTimerRef.current) {
        clearTimeout(iceTimeoutTimerRef.current);
        iceTimeoutTimerRef.current = null;
      }
      if (pcRef.current) {
        console.log(`[HTS RTC ${rtcIdRef.current}] Closing peer connection because: ${reason}`);
        try { pcRef.current.close(); } catch {}
        pcRef.current = null;
      }
    }

    statsInterval = setInterval(async () => {
      if (pcRef.current && pcRef.current.connectionState === 'connected') {
        try {
          const stats = await pcRef.current.getStats();
          stats.forEach(report => {
            if (report.type === 'inbound-rtp' && report.kind === 'video') {
              setWebrtcStats({
                framesDecoded: report.framesDecoded || 0,
                framesDropped: report.framesDropped || 0,
                jitter: report.jitter ? round(report.jitter * 1000, 1) : 0,
                bytesReceived: report.bytesReceived || 0
              });
            }
          });
        } catch {}
      }
    }, 2000);

    initSystem();

    return () => {
      mounted = false;
      if (statsInterval) clearInterval(statsInterval);
      closePeerConnection('component unmounted');
      if (wsRef.current) {
        try { wsRef.current.close(); } catch {}
        wsRef.current = null;
      }
    };
  }, []);

  function round(val, dec = 1) {
    return Math.round(val * Math.pow(10, dec)) / Math.pow(10, dec);
  }

  const handleViewDevice = async (deviceId) => {
    console.log('[HTS Dashboard] Switching active device to:', deviceId);
    setActiveDeviceId(deviceId);
    setDevices(prev => prev.map(d => ({ ...d, is_active: d.id === deviceId })));
    try {
      await apiSetActiveDevice(deviceId);
    } catch (e) {
      console.warn('[HTS Dashboard] Error activating device on backend:', e);
    }
  };

  const handleDisconnectDevice = async (disconnectedDeviceId) => {
    console.log('[HTS Dashboard] Device disconnect requested from UI:', disconnectedDeviceId);
    try {
      await apiDisconnectDevice(disconnectedDeviceId);
    } catch (e) {
      console.warn('[HTS Dashboard] Disconnect REST API catch:', e);
    }

    setDevices(prev => prev.filter(d => d.id !== disconnectedDeviceId));

    if (activeDeviceId === disconnectedDeviceId || !activeDeviceId) {
      if (pcRef.current) {
        try { pcRef.current.close(); } catch {}
        pcRef.current = null;
      }
      setRemoteStream(null);
      setActiveDeviceId('');
      setWebrtcStatus('DISCONNECTED');
    }
  };

  const activeDevice = devices.find(d => d.id === activeDeviceId)
    || devices.find(d => d.is_active)
    || devices[0];

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-brand">
          <span className="brand-dot" />
          <h1>Human Tracking System</h1>
        </div>
        <StatusBar connected={true} deviceCount={devices.length} />
      </header>

      <main className="app-main">
        <CameraFeed
          activeDevice={activeDevice}
          remoteStream={remoteStream}
          webrtcStatus={webrtcStatus}
          webrtcStats={webrtcStats}
        />
        <DevicePanel
          sessionId={sessionId}
          devices={devices}
          setDevices={setDevices}
          activeDeviceId={activeDevice ? activeDevice.id : ''}
          onViewDevice={handleViewDevice}
          onDisconnectDevice={handleDisconnectDevice}
        />
      </main>
    </div>
  );
}
