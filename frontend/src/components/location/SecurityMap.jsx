import { useEffect, useMemo, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useApp } from '../../app/AppProvider';

const icon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

const sleep = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function haversineDistanceKm(a, b) {
  const earthRadiusKm = 6371;
  const toRad = (value) => (value * Math.PI) / 180;
  const dLat = toRad(b[0] - a[0]);
  const dLon = toRad(b[1] - a[1]);
  const lat1 = toRad(a[0]);
  const lat2 = toRad(b[0]);
  const h = Math.sin(dLat / 2) ** 2
    + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
}

function curvedRoute(a, b, segments = 48) {
  const midLat = (a[0] + b[0]) / 2;
  const midLon = (a[1] + b[1]) / 2;
  const dLat = b[0] - a[0];
  const dLon = b[1] - a[1];
  const distance = Math.hypot(dLat, dLon) || 1;

  // Perpendicular offset keeps the route visibly curved without changing
  // the actual distance/time/speed calculations supplied by the backend.
  const bend = clamp(distance * 0.18, 0.08, 12);
  const control = [
    midLat - (dLon / distance) * bend,
    midLon + (dLat / distance) * bend,
  ];

  return Array.from({ length: segments + 1 }, (_, index) => {
    const t = index / segments;
    const oneMinus = 1 - t;
    return [
      oneMinus * oneMinus * a[0] + 2 * oneMinus * t * control[0] + t * t * b[0],
      oneMinus * oneMinus * a[1] + 2 * oneMinus * t * control[1] + t * t * b[1],
    ];
  });
}

function AnimatedViewport({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!points?.length) return undefined;
    const bounds = L.latLngBounds(points);
    const frame = window.requestAnimationFrame(() => {
      map.fitBounds(bounds, {
        padding: [64, 64],
        maxZoom: 10,
        animate: true,
        duration: 1.15,
      });
    });

    return () => window.cancelAnimationFrame(frame);
  }, [map, points]);

  return null;
}

export default function SecurityMap() {
  const { state } = useApp();
  const t = state.transaction;
  const [phase, setPhase] = useState('locating');
  const [routeVisible, setRouteVisible] = useState(false);
  const runId = useRef(0);

  const coordinates = useMemo(() => {
    if (!t) return null;
    const values = [
      Number(t.previous_latitude),
      Number(t.previous_longitude),
      Number(t.current_latitude),
      Number(t.current_longitude),
    ];
    if (!values.every(Number.isFinite)) return null;
    return {
      previous: [values[0], values[1]],
      current: [values[2], values[3]],
    };
  }, [t]);

  const check = state.processingResponse?.checks?.impossible_travel;
  const route = useMemo(
    () => (coordinates ? curvedRoute(coordinates.previous, coordinates.current) : []),
    [coordinates],
  );

  const metrics = useMemo(() => {
    if (!coordinates) return null;

    const backendDistance = Number(check?.distance_km);
    const distanceKm = Number.isFinite(backendDistance)
      ? backendDistance
      : haversineDistanceKm(coordinates.previous, coordinates.current);

    const backendElapsed = Number(check?.time_difference_hours);
    const elapsedHours = Number.isFinite(backendElapsed)
      ? backendElapsed
      : Number(check?.elapsed_hours);

    const speed = Number(check?.required_speed_kmh);
    const calculatedSpeed = Number.isFinite(speed)
      ? speed
      : Number.isFinite(elapsedHours) && elapsedHours > 0
        ? distanceKm / elapsedHours
        : null;

    return {
      distanceKm,
      elapsedHours,
      speedKmh: Number.isFinite(calculatedSpeed) ? calculatedSpeed : null,
      maximumSpeed: Number(check?.max_allowed_speed_kmh ?? check?.maximum_allowed_speed_kmh),
    };
  }, [check, coordinates]);

  useEffect(() => {
    if (!coordinates) return undefined;
    const currentRun = ++runId.current;
    setPhase('locating');
    setRouteVisible(false);

    // The map performs the visual analysis only after the backend result exists.
    const timer = window.setTimeout(async () => {
      if (currentRun !== runId.current) return;
      setPhase('calculating');
      // Reveal the complete route once, instead of redrawing it during each
      // metric calculation. The distance/time/speed cards can continue their
      // own staged reveal without making the route look like it is lagging.
      setRouteVisible(true);
      await sleep(650);
      if (currentRun !== runId.current) return;
      setPhase('distance');
      await sleep(520);
      if (currentRun !== runId.current) return;
      setPhase('time');
      await sleep(520);
      if (currentRun !== runId.current) return;
      setPhase('speed');
      await sleep(520);
      if (currentRun !== runId.current) return;
      setPhase('complete');
    }, 1250);

    return () => window.clearTimeout(timer);
  }, [coordinates]);

  if (!coordinates) return null;

  const mapPoints = [coordinates.previous, coordinates.current];
  const displayRoute = routeVisible ? route : [];
  const checkFailed = check?.passed === false;
  const displayDistance = phase === 'distance' || phase === 'time' || phase === 'speed' || phase === 'complete';
  const displayTime = phase === 'time' || phase === 'speed' || phase === 'complete';
  const displaySpeed = phase === 'speed' || phase === 'complete';
  const routeLabelPosition = route.length ? route[Math.floor(route.length / 2)] : coordinates.current;

  return (
    <div className="map-card">
      <div className="map-heading">
        <div>
          <span className="eyebrow">LOCATION SECURITY</span>
          <h3>Transaction movement</h3>
        </div>
        <span className={`status-badge ${checkFailed ? 'blocked' : 'passed'}`}>
          {checkFailed ? 'BLOCKED' : 'PASS'}
        </span>
      </div>

      <div className="map-shell map-analysis-shell">
        <MapContainer
          center={[(coordinates.previous[0] + coordinates.current[0]) / 2, (coordinates.previous[1] + coordinates.current[1]) / 2]}
          zoom={3}
          scrollWheelZoom={false}
          zoomControl={false}
          style={{ height: '360px', width: '100%' }}
        >
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <AnimatedViewport points={mapPoints} />
          <Marker position={coordinates.previous} icon={icon}>
            <Popup>Previous transaction location</Popup>
          </Marker>
          <Marker position={coordinates.current} icon={icon}>
            <Popup>Current transaction location</Popup>
          </Marker>
          {displayRoute.length > 1 && (
            <Polyline
              positions={displayRoute}
              pathOptions={{ color: '#2563eb', weight: 4, opacity: 0.9 }}
            />
          )}
          {displaySpeed && Number.isFinite(metrics.speedKmh) && (
            <Marker
              position={routeLabelPosition}
              icon={L.divIcon({
                className: 'map-speed-marker',
                html: `<span>${metrics.speedKmh.toFixed(2)} km/h</span>`,
                iconSize: [108, 28],
                iconAnchor: [54, 14],
              })}
              interactive={false}
            />
          )}
        </MapContainer>

        <div className="map-analysis-overlay" aria-live="polite">
          {phase !== 'complete' ? (
            <div className="map-analysis-step">
              <span className="analysis-pulse" />
              <span>
                {phase === 'locating' && 'Locating transaction points…'}
                {phase === 'calculating' && 'Comparing transaction movement…'}
                {phase === 'distance' && 'Calculating distance…'}
                {phase === 'time' && 'Calculating elapsed time…'}
                {phase === 'speed' && 'Calculating travel speed…'}
              </span>
            </div>
          ) : (
            <div className="map-analysis-complete">
              <span className="analysis-check">✓</span>
              <span>Movement analysis complete</span>
            </div>
          )}
        </div>
      </div>

      <div className="map-route-legend">
        <div><span className="route-dot previous" />Previous transaction</div>
        <div><span className="route-dot current" />Current transaction</div>
        <span className="route-note">Backend transaction coordinates</span>
      </div>

      <div className="map-stats animated-map-stats">
        <div className={displayDistance ? 'revealed' : ''}>
          <small>Distance</small>
          <strong>{displayDistance ? `${metrics.distanceKm.toFixed(2)} km` : 'Calculating…'}</strong>
        </div>
        <div className={displayTime ? 'revealed' : ''}>
          <small>Elapsed time</small>
          <strong>{displayTime && Number.isFinite(metrics.elapsedHours) ? `${metrics.elapsedHours.toFixed(4)} h` : 'Calculating…'}</strong>
        </div>
        <div className={`speed-stat ${displaySpeed ? 'revealed' : ''}`}>
          <small>Travel speed</small>
          <strong>{displaySpeed && Number.isFinite(metrics.speedKmh) ? `${metrics.speedKmh.toFixed(2)} km/h` : 'Calculating…'}</strong>
        </div>
        <div>
          <small>Maximum allowed</small>
          <strong>{Number.isFinite(metrics.maximumSpeed) ? `${metrics.maximumSpeed.toFixed(0)} km/h` : '—'}</strong>
        </div>
      </div>

      {displaySpeed && Number.isFinite(metrics.speedKmh) && (
        <div className="map-speed-callout">
          <span className="eyebrow">ROUTE CALCULATION</span>
          <strong>{metrics.speedKmh.toFixed(2)} km/h</strong>
          <span>Required travel speed between the two backend-provided transaction locations.</span>
        </div>
      )}
    </div>
  );
}
