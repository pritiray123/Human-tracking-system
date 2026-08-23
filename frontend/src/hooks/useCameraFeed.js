import { useState, useEffect, useRef } from 'react';

export function useCameraFeed() {
  const [frame,     setFrame]     = useState(null);
  const [fps,       setFps]       = useState(0);
  const [label,     setLabel]     = useState('');
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    function connect() {
      if (cancelled) return;
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/feed`);
      wsRef.current = ws;


      ws.onopen = () => {
        if (!cancelled) setConnected(true);
      };

      ws.onclose = () => {
        if (!cancelled) {
          setConnected(false);
          setFrame(null);
          setTimeout(connect, 2000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      ws.onmessage = (event) => {
        if (cancelled) return;
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'frame') {
            setFrame(msg.frame);
            setFps(msg.fps);
            setLabel(msg.label);
          } else if (msg.type === 'no_camera') {
            setFrame(null);
            setLabel('');
          }
        } catch {
          // ignore malformed messages
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return { frame, fps, label, connected };
}
