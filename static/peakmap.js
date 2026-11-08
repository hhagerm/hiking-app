// Thin wrapper over Leaflet. Owns the map, the tile layers and the markers, and
// knows nothing about the API, the session or claims: the view hands it peaks
// and callbacks, and it reports back when the viewport moves.
//
// Leaflet comes from a CDN <script> in index.html, so it is the global `L`.

const TOPO_URL = "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png";
const OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";

const OSM_CREDIT =
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' +
    " contributors";

// One icon instance backs many markers, which Leaflet allows. The shape lives
// on the inner <i>, because Leaflet writes its own `transform` onto the icon
// element to position it and would clobber ours.
function pinIcon(claimed) {
    return L.divIcon({
        className: claimed ? "peak-pin claimed" : "peak-pin",
        html: "<i></i>",
        iconSize: [16, 22],
        iconAnchor: [8, 20],        // the tip, so the pin points at the summit
        popupAnchor: [0, -18],
    });
}

const ICONS = { plain: pinIcon(false), claimed: pinIcon(true) };

export function createPeakMap(element, options) {
    const {
        center,
        zoom,
        isClaimed,
        popupContent,
        onViewportChange,
        onPopupClose,
    } = options;

    const map = L.map(element, {
        center: [center.lat, center.lon],
        zoom,
        minZoom: 3,
        maxZoom: 17,
    });

    const topo = L.tileLayer(TOPO_URL, {
        maxZoom: 17,
        attribution:
            "Map data: " + OSM_CREDIT + ", SRTM | Style: " +
            '<a href="https://opentopomap.org">OpenTopoMap</a> ' +
            '(<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
    }).addTo(map);

    const standard = L.tileLayer(OSM_URL, {
        maxZoom: 19,
        attribution: OSM_CREDIT,
    });

    L.control.layers({ Topographic: topo, Standard: standard }).addTo(map);

    const group = L.layerGroup().addTo(map);
    const entries = new Map();      // "osm_type/osm_id" -> {peak, marker, claimed}

    map.on("moveend", () => onViewportChange?.());

    // The container is sized by CSS and may not have its final size on the frame
    // the map is created in; Leaflet needs telling once it does.
    requestAnimationFrame(() => map.invalidateSize());

    return {
        bounds: () => map.getBounds(),
        center: () => {
            const c = map.getCenter();
            return { lat: c.lat, lon: c.lng };
        },
        zoom: () => map.getZoom(),

        // Centre-to-corner distance in metres: the radius of the circle that
        // covers the whole rectangular viewport.
        radiusM() {
            return map.getCenter().distanceTo(map.getBounds().getNorthEast());
        },

        // Adds a marker for every peak it has not seen; existing markers are
        // left alone, so panning back neither rebuilds them nor shuts a popup.
        sync(peaks) {
            for (const peak of peaks) {
                const key = `${peak.osm_type}/${peak.osm_id}`;
                if (entries.has(key)) continue;

                const claimed = isClaimed(peak);
                const marker = L.marker([peak.lat, peak.lon], {
                    icon: claimed ? ICONS.claimed : ICONS.plain,
                    title: peak.name ?? "",
                    riseOnHover: true,
                });
                // A function, not a node: the popup is built when it opens, so
                // it always shows the current claim state.
                marker.bindPopup(() => popupContent(peak), { minWidth: 190 });
                marker.on("popupclose", () => onPopupClose?.(key));
                marker.addTo(group);
                entries.set(key, { peak, marker, claimed });
            }
        },

        // Re-applies the claimed/unclaimed icon, skipping markers that did not
        // change so a claim does not rebuild every icon element on screen.
        repaint() {
            for (const entry of entries.values()) {
                const claimed = isClaimed(entry.peak);
                if (claimed === entry.claimed) continue;
                entry.claimed = claimed;
                entry.marker.setIcon(claimed ? ICONS.claimed : ICONS.plain);
            }
        },

        // Pins are hidden rather than dropped when we zoom out past fetching
        // range, so zooming back in needs no refetch.
        setPinsVisible(visible) {
            if (visible && !map.hasLayer(group)) group.addTo(map);
            if (!visible && map.hasLayer(group)) map.removeLayer(group);
        },

        focus(key) {
            const entry = entries.get(key);
            if (!entry) return;
            map.setView(entry.marker.getLatLng(), Math.max(map.getZoom(), 14));
            entry.marker.openPopup();
        },

        // Leaflet keeps window-level resize and scroll handlers alive; without
        // this, every navigation away from the view would leak a live map.
        destroy() {
            map.remove();
            entries.clear();
        },
    };
}
