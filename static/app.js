// Used when the browser won't give us a position (denied, unavailable, no HTTPS).
const FALLBACK = { lat: 50.4575, lon: 14.3701 };

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

async function resolveLocation() {
    const origin = document.getElementById("origin");
    origin.textContent = "Asking your browser for your location...";

    try {
        const position = await getBrowserPosition();
        origin.textContent = `Your location: ${position.lat.toFixed(4)}, ${position.lon.toFixed(4)}`;
        return position;
    } catch (error) {
        origin.textContent =
            `Couldn't get your location (${error.message}) - using ` +
            `${FALLBACK.lat}, ${FALLBACK.lon}.`;
        return FALLBACK;
    }
}

async function loadPeaks(userLocation, radiusM) {
    const status = document.getElementById("status");
    const table = document.getElementById("peaks");
    const tbody = table.querySelector("tbody");

    tbody.replaceChildren();
    table.hidden = true;
    status.textContent = "Loading...";

    const params = new URLSearchParams({
        lat: userLocation.lat,
        lon: userLocation.lon,
        radius_m: radiusM,
    });

    try {
        const response = await fetch(`/peaks/nearby?${params}`);
        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }
        const peaks = await response.json();

        if (peaks.length === 0) {
            status.textContent = `No peaks within ${radiusM} m.`;
            return;
        }

        for (const peak of peaks) {
            const row = tbody.insertRow();
            row.insertCell().textContent = peak.name ?? "(unnamed)";
            row.insertCell().textContent = peak.ele_m === null ? "-" : `${peak.ele_m} m`;
            row.insertCell().textContent = `${Math.round(peak.distance_m)} m`;
        }

        status.textContent = `${peaks.length} peaks within ${radiusM} m.`;
        table.hidden = false;
    } catch (error) {
        status.textContent = `Failed to load peaks: ${error.message}`;
    }
}

const radiusInput = document.getElementById("radius");

// Resolved once on load and reused, so changing the radius doesn't re-prompt.
const userLocation = await resolveLocation();

document.getElementById("controls").addEventListener("submit", (event) => {
    event.preventDefault();
    loadPeaks(userLocation, radiusInput.valueAsNumber);
});

loadPeaks(userLocation, radiusInput.valueAsNumber);
