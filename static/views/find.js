// Homepage: a topographic map of peaks, plus a list of the ones currently in
// view. Both are fed from the same accumulated peak set, so the list is simply
// "what the map is showing", sorted by how far each peak is from you.

import { api } from "../api.js";
import * as session from "../session.js";
import * as claims from "../claims.js";
import { router } from "../router.js";
import { resolveLocation, distanceM } from "../geo.js";
import { createPeakMap } from "../peakmap.js";

// Backend caps, mirrored here so we can tell when a response was truncated:
// /peaks/nearby takes radius_m <= 50_000 and limit <= 200.
const MAX_RADIUS_M = 50_000;
const FETCH_LIMIT = 200;

// Below this zoom one fetch cannot cover the viewport, so we show a hint
// instead of a misleading half-populated map.
const MIN_FETCH_ZOOM = 11;

const DEBOUNCE_MS = 300;
const START_ZOOM = 13;

// Remembered across view switches, so going to the profile and back keeps the
// map where you left it.
let lastView = null;

function el(tag, props = {}, children = []) {
    const node = Object.assign(document.createElement(tag), props);
    node.append(...children);
    return node;
}

function metres(value) {
    return value >= 1000
        ? `${(value / 1000).toFixed(1)} km`
        : `${Math.round(value)} m`;
}

export async function render(container) {
    const origin = el("p", { className: "muted" });
    const mapEl = el("div", { className: "map" });
    const status = el("p", { className: "status" });
    const tbody = el("tbody");
    const table = el("table", { hidden: true }, [
        el("thead", {}, [
            el("tr", {}, [
                el("th", { textContent: "Name" }),
                el("th", { textContent: "Elevation" }),
                el("th", { textContent: "Distance" }),
                el("th", { textContent: "" }),
            ]),
        ]),
        tbody,
    ]);

    container.append(el("h1", { textContent: "Find peaks" }), origin, mapEl,
                     status, table);

    let peakMap = null;             // the Leaflet wrapper, once we have a centre
    let location = null;            // where you are, for the distance column
    const peaks = new Map();        // every peak we have fetched, by key
    const covered = [];             // viewports we hold complete data for
    const rowButtons = new Map();   // key -> claim button in the list
    let popupButton = null;         // {key, button} of the open popup, if any
    let debounce = null;
    let fetchToken = 0;

    function setStatus(text, isError = false) {
        status.textContent = text;
        status.classList.toggle("error", isError);
    }

    // ---- claim state painting ---------------------------------------------

    function paintButton(peak, button) {
        const claimed = claims.isClaimed(peak);
        button.textContent = claimed ? "Claimed" : "Claim";
        button.className = claimed ? "claim claimed" : "claim";
        button.setAttribute("aria-pressed", String(claimed));
    }

    async function onClaimClick(peak, button) {
        if (!session.isLoggedIn()) {
            router.navigate("#/login");
            return;
        }
        button.disabled = true;
        try {
            await claims.toggle(peak);
        } catch (error) {
            setStatus(`Could not save that: ${error.message}`, true);
        } finally {
            button.disabled = false;
        }
    }

    function claimButton(peak) {
        const button = el("button", { type: "button" });
        paintButton(peak, button);
        button.addEventListener("click", () => void onClaimClick(peak, button));
        return button;
    }

    // One subscription repaints the list, the open popup and the pins.
    const stop = claims.onChange(() => {
        for (const [key, button] of rowButtons) {
            const peak = peaks.get(key);
            if (peak) paintButton(peak, button);
        }
        if (popupButton) {
            const peak = peaks.get(popupButton.key);
            if (peak) paintButton(peak, popupButton.button);
        }
        peakMap?.repaint();
    });

    // ---- the popup --------------------------------------------------------

    function popupContent(peak) {
        const button = claimButton(peak);
        popupButton = { key: claims.key(peak), button };

        const facts = [];
        if (peak.ele_m !== null) facts.push(`${Math.round(peak.ele_m)} m`);
        if (location) facts.push(`${metres(distanceM(location, peak))} away`);

        return el("div", { className: "peak-popup" }, [
            el("strong", { textContent: peak.name ?? "(unnamed)" }),
            el("p", {
                className: "muted",
                textContent: facts.join(" · ") || "no elevation recorded",
            }),
            button,
        ]);
    }

    // ---- the list ---------------------------------------------------------

    function visiblePeaks() {
        const bounds = peakMap.bounds();
        const rows = [];
        for (const peak of peaks.values()) {
            if (bounds.contains([peak.lat, peak.lon])) rows.push(peak);
        }
        if (location) {
            rows.sort((a, b) => distanceM(location, a) - distanceM(location, b));
        }
        return rows;
    }

    function renderList() {
        tbody.replaceChildren();
        rowButtons.clear();

        if (peakMap.zoom() < MIN_FETCH_ZOOM) {
            table.hidden = true;
            return 0;
        }

        const rows = visiblePeaks();
        for (const peak of rows) {
            const key = claims.key(peak);
            const button = claimButton(peak);
            rowButtons.set(key, button);

            const name = el("button", {
                type: "button",
                className: "link",
                textContent: peak.name ?? "(unnamed)",
                title: "Show on the map",
            });
            name.addEventListener("click", () => peakMap.focus(key));

            const row = tbody.insertRow();
            row.insertCell().append(name);
            row.insertCell().textContent =
                peak.ele_m === null ? "-" : `${Math.round(peak.ele_m)} m`;
            row.insertCell().textContent =
                location ? metres(distanceM(location, peak)) : "-";
            row.insertCell().append(button);
        }
        table.hidden = rows.length === 0;
        return rows.length;
    }

    // ---- fetching ---------------------------------------------------------

    async function fetchViewport() {
        if (peakMap.zoom() < MIN_FETCH_ZOOM) {
            peakMap.setPinsVisible(false);
            renderList();
            setStatus("Zoom in to see peaks.");
            return;
        }
        peakMap.setPinsVisible(true);

        const bounds = peakMap.bounds();
        if (covered.some((done) => done.contains(bounds))) {
            setStatus(`${renderList()} peaks in view.`);
            return;
        }

        // /peaks/nearby is a circle and a viewport is a rectangle, so we ask for
        // the circle that contains the rectangle and over-fetch the corners.
        const wanted = Math.ceil(peakMap.radiusM());
        const radiusM = Math.min(wanted, MAX_RADIUS_M);
        const centre = peakMap.center();

        const token = ++fetchToken;
        setStatus("Loading peaks...");
        try {
            const rows = await api.nearbyPeaks({
                lat: centre.lat, lon: centre.lon, radiusM, limit: FETCH_LIMIT,
            });
            if (token !== fetchToken) return;    // a newer fetch superseded us

            for (const peak of rows) peaks.set(claims.key(peak), peak);
            peakMap.sync(rows);

            // Only remember this viewport as done when the answer was complete:
            // a truncated or radius-clamped response leaves holes at the edges.
            const truncated = rows.length >= FETCH_LIMIT;
            const clamped = radiusM < wanted;
            if (!truncated && !clamped) covered.push(bounds);

            const shown = renderList();
            setStatus(truncated
                ? `${shown} peaks in view - showing the ${FETCH_LIMIT} nearest, ` +
                  "zoom in for the rest."
                : `${shown} peaks in view.`);
        } catch (error) {
            if (token !== fetchToken) return;
            setStatus(`Failed to load peaks: ${error.message}`, true);
        }
    }

    function onViewportChange() {
        // The list tracks panning right away; the fetch waits for you to stop.
        if (peakMap.zoom() >= MIN_FETCH_ZOOM) renderList();
        clearTimeout(debounce);
        debounce = setTimeout(() => void fetchViewport(), DEBOUNCE_MS);
    }

    // ---- start up ---------------------------------------------------------

    origin.textContent = "Asking your browser for your location...";
    location = await resolveLocation();
    origin.textContent = location.fallback
        ? `Could not get your location (${location.error}) - starting from ` +
          `${location.lat}, ${location.lon}.`
        : `Your location: ${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}`;

    // Load the claimed set before any pin or row is painted, so nothing flashes
    // as unclaimed. Anonymous users get an empty set.
    await claims.load(session.getUser()).catch(() => null);

    peakMap = createPeakMap(mapEl, {
        center: lastView?.center ?? { lat: location.lat, lon: location.lon },
        zoom: lastView?.zoom ?? START_ZOOM,
        isClaimed: claims.isClaimed,
        popupContent,
        onViewportChange,
        onPopupClose: (key) => {
            if (popupButton?.key === key) popupButton = null;
        },
    });

    await fetchViewport();

    return () => {
        clearTimeout(debounce);
        lastView = { center: peakMap.center(), zoom: peakMap.zoom() };
        stop();
        peakMap.destroy();
    };
}
