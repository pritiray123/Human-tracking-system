export default function StatusBar({ connected, deviceCount }) {
  return (
    <div className="status-bar">
      <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`} />
      <span className="status-text">
        {connected
          ? `Backend connected — ${deviceCount} device${deviceCount !== 1 ? 's' : ''}`
          : 'Connecting to backend…'}
      </span>
    </div>
  );
}
