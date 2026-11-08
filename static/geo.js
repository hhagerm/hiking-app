// Geolocation, resolved once per page load and shared. Switching views must not
// re-prompt the user, so the promise is memoized.

// Used when the browser won't give us a position (denied, unavailable, no HTTPS).
export const FALLBACK = { lat: 50.4575, lon: 14.3701 };

let pending = null;

function getBrowserPosition() {
    // getCurrentPosition is callback-based; wrap it so we can await it.
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error("geolocation unsupported"));
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (position) => resolve({
                lat: position.coords.latitude,
                lon: position.coords.longitude,
            }),
            (error) => reject(new Error(error.message)),
            { timeout: 10000 },
        );
    });
}

async function resolve() {
    try {
        const position = await getBrowserPosition();
        return { ...position, fallback: false, error: null };
    } catch (error) {
        return { ...FALLBACK, fallback: true, error: error.message };
    }
}

// Always resolves; check `.fallback` to see whether it's the real position.
export function resolveLocation() {
    if (!pending) pending = resolve();
    return pending;
}

// Great-circle distance in metres between two {lat, lon} points (haversine).
// The map list needs "how far is this peak from me", and /peaks/nearby's
// distance_m is measured from whatever centre we happened to fetch around.
export function distanceM(a, b) {
    const R = 6371008.8;                 // mean Earth radius, metres
    const toRad = (deg) => (deg * Math.PI) / 180;

    const dLat = toRad(b.lat - a.lat);
    const dLon = toRad(b.lon - a.lon);
    const h = Math.sin(dLat / 2) ** 2 +
              Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) *
              Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
}
