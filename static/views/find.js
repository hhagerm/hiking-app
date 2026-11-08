// Homepage: peaks near you, with a claim button on each row.

import { api, ApiError } from "../api.js";
import * as session from "../session.js";
import * as claims from "../claims.js";
import { router } from "../router.js";
import { resolveLocation } from "../geo.js";

// Remembered across view switches so going to the profile and back keeps it.
let radiusM = 5000;

function el(tag, props = {}, children = []) {
    const node = Object.assign(document.createElement(tag), props);
    node.append(...children);
    return node;
}

export async function render(container) {
    const origin = el("p", { className: "muted" });
    const radius = el("input", {
        type: "number", id: "radius", name: "radius",
        value: String(radiusM), min: "100", step: "100", required: true,
    });
    const form = el("form", { className: "controls" }, [
        el("label", { htmlFor: "radius", textContent: "Max distance (m)" }),
        radius,
        el("button", { type: "submit", textContent: "Search" }),
    ]);
    const status = el("p", { className: "status", textContent: "Loading..." });
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

    container.append(el("h1", { textContent: "Nearby peaks" }), origin, form,
                     status, table);

    // key -> button, so a claims change repaints without refetching.
    const buttons = new Map();

    function paintButton(peak, button) {
        const claimed = claims.isClaimed(peak);
        button.textContent = claimed ? "Claimed" : "Claim";
        button.className = claimed ? "claim claimed" : "claim";
        button.setAttribute("aria-pressed", String(claimed));
    }

    const stop = claims.onChange(() => {
        for (const [, { peak, button }] of buttons) paintButton(peak, button);
    });

    async function onClaimClick(peak, button) {
        if (!session.isLoggedIn()) {
            router.navigate("#/login");
            return;
        }
        button.disabled = true;
        try {
            await claims.toggle(peak);
        } catch (error) {
            status.textContent = `Could not save that: ${error.message}`;
            status.classList.add("error");
        } finally {
            button.disabled = false;
        }
    }

    function addRow(peak) {
        const button = el("button", { type: "button" });
        paintButton(peak, button);
        button.addEventListener("click", () => void onClaimClick(peak, button));
        buttons.set(claims.key(peak), { peak, button });

        const row = tbody.insertRow();
        row.insertCell().textContent = peak.name ?? "(unnamed)";
        row.insertCell().textContent =
            peak.ele_m === null ? "-" : `${peak.ele_m} m`;
        row.insertCell().textContent = `${Math.round(peak.distance_m)} m`;
        row.insertCell().append(button);
    }

    async function load(location) {
        tbody.replaceChildren();
        buttons.clear();
        table.hidden = true;
        status.classList.remove("error");
        status.textContent = "Loading...";

        try {
            // The claimed set is needed to paint the buttons; load it first so
            // rows never flash as unclaimed. Anonymous users get an empty set.
            const [peaks] = await Promise.all([
                api.nearbyPeaks({ lat: location.lat, lon: location.lon, radiusM }),
                claims.load(session.getUser()).catch(() => null),
            ]);

            if (peaks.length === 0) {
                status.textContent = `No peaks within ${radiusM} m.`;
                return;
            }
            for (const peak of peaks) addRow(peak);
            status.textContent = `${peaks.length} peaks within ${radiusM} m.`;
            table.hidden = false;
        } catch (error) {
            status.textContent = `Failed to load peaks: ${error.message}`;
            status.classList.add("error");
        }
    }

    origin.textContent = "Asking your browser for your location...";
    const location = await resolveLocation();
    origin.textContent = location.fallback
        ? `Couldn't get your location (${location.error}) - using ` +
          `${location.lat}, ${location.lon}.`
        : `Your location: ${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}`;

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        if (!radius.valueAsNumber) return;
        radiusM = radius.valueAsNumber;
        void load(location);
    });

    await load(location);
    return stop;
}
