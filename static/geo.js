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
