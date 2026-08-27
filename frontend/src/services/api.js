const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export function getPublicUrl() {
  return API_BASE || window.location.origin;
}

export function getApiUrl(path) {
  if (!API_BASE) return path;
  return `${API_BASE}${path}`;
}

export function getWsSignalingUrl() {
  const wsEnv = import.meta.env.VITE_WS_URL;
  if (wsEnv) return wsEnv;

  if (API_BASE) {
    const wsProto = API_BASE.startsWith('https:') ? 'wss:' : 'ws:';
    const host = API_BASE.replace(/^https?:\/\//, '');
    return `${wsProto}//${host}/ws/signaling`;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/signaling`;
}

export async function createSession() {
  const url = getApiUrl('/api/session/new');
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error(`POST /api/session/new failed: ${res.status}`);
  return res.json();
}

export async function getDevices() {
  const url = getApiUrl('/api/devices');
  const res = await fetch(url);
  if (!res.ok) throw new Error(`GET /api/devices failed: ${res.status}`);
  return res.json();
}

export async function setActiveDevice(deviceId) {
  const url = getApiUrl(`/api/devices/${encodeURIComponent(deviceId)}/active`);
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error(`POST .../active failed: ${res.status}`);
  return res.json();
}

export async function disconnectDevice(deviceId) {
  const url = getApiUrl(`/api/devices/${encodeURIComponent(deviceId)}/disconnect`);
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error(`POST .../disconnect failed: ${res.status}`);
  return res.json();
}

export async function getSystemInfo() {
  const url = getApiUrl('/api/info');
  const res = await fetch(url);
  if (!res.ok) throw new Error(`GET /api/info failed: ${res.status}`);
  return res.json();
}

export function getActiveStreamUrl(activeDeviceId) {
  const base = getApiUrl('/api/stream/active');
  if (!activeDeviceId) return base;
  return `${base}?dev=${encodeURIComponent(activeDeviceId)}`;
}

export function getStreamerPageUrl(sessionId) {
  const base = getApiUrl('/api/streamer');
  if (sessionId) return `${base}?session=${encodeURIComponent(sessionId)}`;
  return base;
}

export async function setLocalSourceCamera() {
  const url = getApiUrl('/api/devices/local/source/camera');
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error(`POST /api/devices/local/source/camera failed: ${res.status}`);
  return res.json();
}

export async function setLocalSourceVideo(file) {
  const url = getApiUrl('/api/devices/local/source/video');
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(url, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error(`POST /api/devices/local/source/video failed: ${res.status}`);
  return res.json();
}

export async function controlDeviceVideo(deviceId, action, params = {}) {
  const url = getApiUrl(`/api/devices/${encodeURIComponent(deviceId)}/control`);
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, ...params })
  });
  if (!res.ok) throw new Error(`POST /api/devices/${deviceId}/control failed: ${res.status}`);
  return res.json();
}

export async function setDeviceTracking(deviceId, enabled) {
  const url = getApiUrl(`/api/devices/${encodeURIComponent(deviceId)}/tracking`);
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled: Boolean(enabled) })
  });
  if (!res.ok) throw new Error(`POST /api/devices/${deviceId}/tracking failed: ${res.status}`);
  return res.json();
}

export async function getDeviceAnalytics(deviceId) {
  const url = getApiUrl(`/api/devices/${encodeURIComponent(deviceId)}/analytics`);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`GET /api/devices/${deviceId}/analytics failed: ${res.status}`);
  return res.json();
}


