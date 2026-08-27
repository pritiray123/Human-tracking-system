import { useState, useEffect, useRef } from 'react';
import { getDeviceAnalytics, setDeviceTracking } from '../services/api';

export default function AnalyticsPanel({ activeDevice, onToggleTracking }) {
  const [stats, setStats] = useState({
    peopleCount: 0,
    maxPeople: 0,
    activeTrackIds: [],
    inferenceMs: 0,
    fps: 0,
    trackingEnabled: false
  });
  const [samples, setSamples] = useState([]);
  const [events, setEvents] = useState([]);
  const [isToggling, setIsToggling] = useState(false);

  // Per-device history cache stored in ref to maintain isolated history per device
  const deviceHistoryRef = useRef({});

  const deviceId = activeDevice?.id || '';
  const isTrackingOn = Boolean(activeDevice?.tracking_enabled);

  useEffect(() => {
    if (!deviceId) return;

    // Ensure state object exists for deviceId
    if (!deviceHistoryRef.current[deviceId]) {
      deviceHistoryRef.current[deviceId] = {
        maxPeople: 0,
        samples: [],
        events: [],
        prevTrackIds: [],
        prevCount: null
      };
    }

    const currentHistory = deviceHistoryRef.current[deviceId];
    setSamples(currentHistory.samples);
    setEvents(currentHistory.events);
    setStats({
      peopleCount: currentHistory.prevCount || 0,
      maxPeople: currentHistory.maxPeople,
      activeTrackIds: currentHistory.prevTrackIds,
      inferenceMs: 0,
      fps: 0,
      trackingEnabled: isTrackingOn
    });
  }, [deviceId, isTrackingOn]);

  useEffect(() => {
    if (!deviceId || !isTrackingOn) return;

    let mounted = true;
    const interval = setInterval(async () => {
      try {
        const data = await getDeviceAnalytics(deviceId);
        if (!mounted) return;

        const timeStr = new Date().toLocaleTimeString('en-GB', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });

        const history = deviceHistoryRef.current[deviceId] || {
          maxPeople: 0,
          samples: [],
          events: [],
          prevTrackIds: [],
          prevCount: null
        };

        const currentCount = data.people_count || 0;
        const currentTrackIds = data.active_track_ids || [];
        const newMax = Math.max(history.maxPeople, currentCount);
        history.maxPeople = newMax;

        // Bounded samples queue (max 50)
        const updatedSamples = [...history.samples, { time: timeStr, count: currentCount }].slice(-50);
        history.samples = updatedSamples;

        // Detect event timeline changes
        const newEvents = [...history.events];

        // Track IDs that arrived
        currentTrackIds.forEach(id => {
          if (!history.prevTrackIds.includes(id)) {
            newEvents.unshift({
              id: `${timeStr}-${id}-enter`,
              time: timeStr,
              text: `Human #${id} detected`,
              type: 'enter'
            });
          }
        });

        // Count changed
        if (history.prevCount !== null && history.prevCount !== currentCount) {
          newEvents.unshift({
            id: `${timeStr}-count-${currentCount}`,
            time: timeStr,
            text: `People count changed: ${history.prevCount} → ${currentCount}`,
            type: 'change'
          });
        }

        // Track IDs that left
        history.prevTrackIds.forEach(id => {
          if (!currentTrackIds.includes(id)) {
            newEvents.unshift({
              id: `${timeStr}-${id}-leave`,
              time: timeStr,
              text: `Human #${id} left frame`,
              type: 'leave'
            });
          }
        });

        const boundedEvents = newEvents.slice(0, 25);
        history.events = boundedEvents;
        history.prevTrackIds = currentTrackIds;
        history.prevCount = currentCount;
        deviceHistoryRef.current[deviceId] = history;

        setSamples(updatedSamples);
        setEvents(boundedEvents);
        setStats({
          peopleCount: currentCount,
          maxPeople: newMax,
          activeTrackIds: currentTrackIds,
          inferenceMs: data.inference_ms || 0,
          fps: data.fps || 0,
          trackingEnabled: Boolean(data.tracking_enabled)
        });
      } catch (err) {
        console.warn('[AnalyticsPanel] Fetch stats catch:', err);
      }
    }, 500);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [deviceId, isTrackingOn]);

  const handleToggleTracking = async () => {
    if (!activeDevice || isToggling) return;
    setIsToggling(true);
    try {
      const target = !isTrackingOn;
      const res = await setDeviceTracking(activeDevice.id, target);
      if (res && res.success) {
        onToggleTracking?.(activeDevice.id, res.tracking_enabled);
      }
    } catch (e) {
      console.error('[AnalyticsPanel] Toggle tracking error:', e);
    } finally {
      setIsToggling(false);
    }
  };

  if (!activeDevice) {
    return (
      <div className="analytics-panel">
        <div className="analytics-header">
          <h2>LIVE HUMAN ANALYTICS</h2>
        </div>
        <div className="analytics-inactive">
          <span className="inactive-icon">📡</span>
          <p className="inactive-title">NO DEVICE SELECTED</p>
          <p className="inactive-sub">Select an active camera to view telemetry.</p>
        </div>
      </div>
    );
  }

  if (!isTrackingOn) {
    return (
      <div className="analytics-panel">
        <div className="analytics-header">
          <h2>LIVE HUMAN ANALYTICS</h2>
        </div>

        <div className="analytics-inactive">
          <span className="inactive-icon">🤖</span>
          <p className="inactive-title">AI TRACKING OFF</p>
          <p className="inactive-sub">Enable Human Tracking to view live analytics.</p>
          <button
            onClick={handleToggleTracking}
            disabled={isToggling}
            className="btn-enable-analytics"
          >
            {isToggling ? 'Enabling…' : '⚡ Enable Human Tracking'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-panel">
      <div className="analytics-header">
        <h2>LIVE HUMAN ANALYTICS</h2>
        <span className="live-indicator">
          <span className="live-dot" /> LIVE
        </span>
      </div>

      {/* Primary Metrics Grid */}
      <div className="analytics-stats-grid">
        <div className="stat-card accent">
          <span className="stat-label">👥 Current People</span>
          <span className="stat-value">{stats.peopleCount}</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">📈 Max Detected</span>
          <span className="stat-value">{stats.maxPeople}</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">🎯 Tracking IDs</span>
          <span className="stat-value track-ids">
            {stats.activeTrackIds.length > 0 ? stats.activeTrackIds.map(id => `#${id}`).join(', ') : 'None'}
          </span>
        </div>

        <div className="stat-card">
          <span className="stat-label">⚡ AI Inference</span>
          <span className="stat-value">{stats.inferenceMs} <small>ms</small></span>
        </div>

        <div className="stat-card">
          <span className="stat-label">🎥 Stream FPS</span>
          <span className="stat-value">{stats.fps}</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">🟢 Status</span>
          <span className="stat-value status-on">ON</span>
        </div>
      </div>

      {/* Real-time People Count Chart */}
      <div className="analytics-chart-section">
        <h3>People Detected Over Time</h3>
        <PeopleCountChart samples={samples} maxPeople={stats.maxPeople} />
      </div>

      {/* Recent Activity Timeline */}
      <div className="analytics-timeline-section">
        <h3>RECENT ACTIVITY</h3>
        <div className="timeline-list">
          {events.length === 0 ? (
            <div className="timeline-empty">Monitoring active stream…</div>
          ) : (
            events.map(ev => (
              <div key={ev.id} className={`timeline-item ${ev.type}`}>
                <span className="timeline-time">{ev.time}</span>
                <span className="timeline-text">{ev.text}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// Lightweight React SVG Line/Area Chart Component
function PeopleCountChart({ samples, maxPeople }) {
  const width = 280;
  const height = 130;
  const padding = { top: 15, right: 15, bottom: 25, left: 30 };

  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  // Determine Y-axis max scale
  const dataMax = samples.reduce((acc, s) => Math.max(acc, s.count), 0);
  const yMax = Math.max(5, Math.ceil((Math.max(dataMax, maxPeople) + 1) / 2) * 2);

  if (samples.length < 2) {
    return (
      <div className="chart-placeholder">
        <span>Collecting telemetry samples…</span>
      </div>
    );
  }

  const pointStep = chartW / Math.max(1, samples.length - 1);
  const points = samples.map((s, idx) => {
    const x = padding.left + idx * pointStep;
    const y = padding.top + chartH - (s.count / yMax) * chartH;
    return { x, y, count: s.count, time: s.time };
  });

  const lineD = points.reduce((acc, p, idx) => {
    return `${acc} ${idx === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
  }, '');

  const lastP = points[points.length - 1];
  const firstP = points[0];
  const areaD = `${lineD} L ${lastP.x.toFixed(1)} ${(padding.top + chartH).toFixed(1)} L ${firstP.x.toFixed(1)} ${(padding.top + chartH).toFixed(1)} Z`;

  // Grid lines
  const gridTicks = [0, yMax / 2, yMax];

  return (
    <div className="svg-chart-container">
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <linearGradient id="analyticsGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00c896" stopOpacity="0.45" />
            <stop offset="100%" stopColor="#00c896" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Gridlines & Y-labels */}
        {gridTicks.map((val, i) => {
          const y = padding.top + chartH - (val / yMax) * chartH;
          return (
            <g key={i}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="#2a2a45"
                strokeDasharray="2,2"
                strokeWidth="1"
              />
              <text
                x={padding.left - 6}
                y={y + 3}
                fill="#888"
                fontSize="9"
                textAnchor="end"
              >
                {Math.round(val)}
              </text>
            </g>
          );
        })}

        {/* Gradient Area */}
        <path d={areaD} fill="url(#analyticsGradient)" />

        {/* Line Stroke */}
        <path d={lineD} fill="none" stroke="#00c896" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

        {/* Pulsing Live Dot on latest point */}
        <circle cx={lastP.x} cy={lastP.y} r="4" fill="#00c896" />
        <circle cx={lastP.x} cy={lastP.y} r="7" fill="none" stroke="#00c896" strokeWidth="1.5" opacity="0.6">
          <animate attributeName="r" values="4;10;4" dur="2s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.8;0;0.8" dur="2s" repeatCount="indefinite" />
        </circle>

        {/* Axis Labels */}
        <text x={padding.left} y={height - 5} fill="#666" fontSize="9">
          {samples[0]?.time}
        </text>
        <text x={width - padding.right} y={height - 5} fill="#666" fontSize="9" textAnchor="end">
          {lastP.time}
        </text>
      </svg>
    </div>
  );
}
