// Every call to the backend lives here. Views must not fetch directly, so a
// change to a URL or payload shape is a change to this file only.

export class ApiError extends Error {
    constructor(status, fieldErrors, message) {
        super(message || `request failed with ${status}`);
        this.name = "ApiError";
        this.status = status;
        this.fieldErrors = fieldErrors;
    }

    // Convenience for forms: the message for a field, if any.
    for(field) {
        return this.fieldErrors[field] ?? null;
    }
}

// The backend speaks two error shapes:
//   our handlers      -> {"errors": [{"field": "email", "message": "..."}]}
//   FastAPI validation-> {"detail": [{"loc": ["query", "osm_id"], "msg": "..."}]}
// Normalize both to {field: message}. A null/absent field becomes "_".
function parseErrors(payload) {
    const fieldErrors = {};
    if (!payload || typeof payload !== "object") return fieldErrors;

    if (Array.isArray(payload.errors)) {
        for (const e of payload.errors) {
            fieldErrors[e.field ?? "_"] = e.message ?? "invalid";
        }
    } else if (Array.isArray(payload.detail)) {
        for (const e of payload.detail) {
            const loc = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : "_";
            fieldErrors[loc ?? "_"] = e.msg ?? "invalid";
        }
    } else if (typeof payload.detail === "string") {
        fieldErrors._ = payload.detail;
    }
    return fieldErrors;
}

async function request(method, path, { body, query } = {}) {
    const url = query ? `${path}?${new URLSearchParams(query)}` : path;
    const init = { method, headers: {} };
    if (body !== undefined) {
        init.headers["Content-Type"] = "application/json";
        init.body = JSON.stringify(body);
    }

    let response;
    try {
        response = await fetch(url, init);
    } catch (cause) {
        // Network-level failure: server down, DNS, offline.
        throw new ApiError(0, { _: "could not reach the server" },
                           "could not reach the server");
    }

    if (response.status === 204) return null;

    const text = await response.text();
    let payload = null;
    if (text) {
        try {
            payload = JSON.parse(text);
        } catch {
            payload = null;          // e.g. the bare "Internal Server Error"
        }
    }

    if (!response.ok) {
        const fieldErrors = parseErrors(payload);
        const first = Object.values(fieldErrors)[0];
        throw new ApiError(response.status, fieldErrors,
                           first || `${response.status} ${response.statusText}`);
    }
    return payload;
}

export const api = {
    // --- auth -------------------------------------------------------------
    me: () => request("GET", "/user/me"),

    login: (username, password) =>
        request("POST", "/user/login", { body: { username, password } }),

    register: (email, username, password1, password2) =>
        request("POST", "/user/register",
                { body: { email, username, password1, password2 } }),

    // Not implemented on the backend yet; session.logout() tolerates 404/405.
    logout: () => request("DELETE", "/user/session"),

    // --- peaks ------------------------------------------------------------
    nearbyPeaks: ({ lat, lon, radiusM, limit }) =>
        request("GET", "/peaks/nearby", {
            query: {
                lat,
                lon,
                radius_m: radiusM,
                ...(limit === undefined ? {} : { limit }),
            },
        }),

    // --- collection -------------------------------------------------------
    collection: () => request("GET", "/collection/list"),

    claim: (poi) =>
        request("POST", "/collection/claim",
                { query: { osm_type: poi.osm_type, osm_id: poi.osm_id } }),

    unclaim: (poi) =>
        request("POST", "/collection/unclaim",
                { query: { osm_type: poi.osm_type, osm_id: poi.osm_id } }),
};
