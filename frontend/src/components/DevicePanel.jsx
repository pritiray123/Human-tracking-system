import { useState, useEffect } from 'react';
import {
  getDevices,
  setActiveDevice,
  disconnectDevice,
  getSystemInfo,
  getPublicUrl
} from '../services/api';

export default function DevicePanel({
  sessionId,
  devices,
  setDevices,
  activeDeviceId,
  onViewDevice,
  onDisconnectDevice
}) {
  const [loading, setLoading] = useState(false);
  const [streamerUrl, setStreamerUrl] = useState('');
  const [publicStreamerUrl, setPublicStreamerUrl] = useState('');
  const [turnConfigured, setTurnConfigured] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function fetchInfo() {
      try {
        const info = await getSystemInfo();
        if (!mounted) return;
        setStreamerUrl(info.streamer_url || '');
        setPublicStreamerUrl(info.public_streamer_url || '');
        setTurnConfigured(info.turn_configured ?? false);
      } catch (error) {
        console.error('[HTS UI] Failed to fetch system info:', error);
      }
    }

    async function fetchDevices() {
      try {
        const data = await getDevices();
        if (!mounted) return;
        setDevices(data);
      } catch (error) {
        console.error('[HTS UI] Failed to fetch devices:', error);
      }
    }

    fetchInfo();
    fetchDevices();

    const interval = setInterval(fetchDevices, 1000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [setDevices]);

  async function handleView(deviceId) {
    console.log('[HTS UI] Viewing device:', deviceId);
    setLoading(true);
    try {
      const result = await setActiveDevice(deviceId);
      console.log('[HTS UI] Active device response:', result);
      onViewDevice?.(deviceId);
    } catch (error) {
      console.error('[HTS UI] Failed to set active device:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleDisconnect(deviceId) {
    console.log('[HTS UI] User pressed Disconnect for device:', deviceId);
    setLoading(true);
    try {
      await disconnectDevice(deviceId);
      setDevices(prev => prev.filter(device => device.id !== deviceId));
      onDisconnectDevice?.(deviceId);
    } catch (error) {
      console.error('[HTS UI] Failed to disconnect device:', error);
    } finally {
      setLoading(false);
    }
  }

  const baseLocal = streamerUrl || `http://${window.location.hostname}:8000/api/streamer`;
  const localPairUrl = sessionId ? `${baseLocal}?session=${sessionId}` : baseLocal;

  const basePublic = publicStreamerUrl || `${getPublicUrl()}/api/streamer`;
  const publicPairUrl = sessionId ? `${basePublic}?session=${sessionId}` : basePublic;

  return (
    <div className="device-panel">
      <h2>Device Manager</h2>

      {!turnConfigured && (
        <div
          style={{
            background: '#332200',
            border: '1px solid #ffaa00',
            borderRadius: '8px',
            padding: '10px 12px',
            fontSize: '0.75rem',
            color: '#ffcc00',
            marginBottom: '12px'
          }}
        >
          ⚠️ <strong>TURN relay not configured</strong>
          {' — '}
          Direct P2P WebRTC may fail across mobile data/different networks. System will automatically use Fallback JPEG streaming.
        </div>
      )}

      <div className="remote-url-box">
        <p className="remote-url-label">Remote Camera Pairing Session:</p>

        {sessionId && (
          <p className="remote-url-hint" style={{ color: '#00c896', fontWeight: 700 }}>
            Session ID: {sessionId}
          </p>
        )}

        <p className="remote-url-hint" style={{ marginTop: '4px' }}>
          Public Internet Mode (Mobile Data / Remote Wi-Fi):
        </p>

        <a
          href={publicPairUrl}
          target="_blank"
          rel="noreferrer"
          className="remote-url-link"
          style={{ color: '#00e5a3' }}
        >
          {publicPairUrl}
        </a>

        <p className="remote-url-hint" style={{ marginTop: '8px' }}>
          Local LAN (Same Wi-Fi):
        </p>

        <a href={localPairUrl} target="_blank" rel="noreferrer" className="remote-url-link">
          {localPairUrl}
        </a>
      </div>

      <div className="devices-section">
        <h3>Connected Devices</h3>

        {devices.length === 0 ? (
          <p className="no-devices">No cameras connected.</p>
        ) : (
          <ul className="device-list">
            {devices.map(dev => {
              const isActive = dev.id === activeDeviceId || dev.is_active;
              const statusText = dev.status || (dev.is_open ? 'STREAMING' : 'WAITING');
              const latencyText = dev.latency_ms > 0 ? ` · ${dev.latency_ms} ms` : '';

              return (
                <li key={dev.id} className={`device-item ${isActive ? 'active' : ''}`}>
                  <div className="device-info">
                    <span className={`device-status-dot ${dev.is_open ? 'open' : 'closed'}`} />
                    <div>
                      <p className="device-label">{dev.label}</p>
                      <p className="device-meta">
                        {dev.width > 0 ? `${dev.width}×${dev.height} · ` : ''}
                        Status:{' '}
                        <strong
                          style={{
                            color: statusText.toUpperCase() === 'STREAMING'
                              ? '#00c896'
                              : '#ffaa00'
                          }}
                        >
                          {statusText}{latencyText}
                        </strong>
                        {isActive && ' · ACTIVE'}
                      </p>
                    </div>
                  </div>

                  <div className="device-actions">
                    <button
                      className="btn-view"
                      onClick={() => handleView(dev.id)}
                      disabled={loading || isActive}
                    >
                      {isActive ? 'Active' : 'View'}
                    </button>

                    <button
                      className="btn-disconnect"
                      onClick={() => handleDisconnect(dev.id)}
                      disabled={loading}
                    >
                      Disconnect
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}