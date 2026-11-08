// Owns the set of POIs the logged-in user has claimed, and the claim/unclaim
// actions. Shared by the peak table and (later) map markers, so the optimistic
// toggle lives here and renderers only render.

import { api } from "./api.js";

let claimed = new Set();
let loadedFor = null;            // user id the set was loaded for
const listeners = new Set();

function emit() {
    for (const fn of listeners) fn(claimed);
}

export function key(poi) {
    return `${poi.osm_type}/${poi.osm_id}`;
}

export function isClaimed(poi) {
    return claimed.has(key(poi));
}

export function count() {
    return claimed.size;
}

// Returns an unsubscribe function.
export function onChange(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
}

// Called by session.js whenever the current user changes.
export function reset() {
    claimed = new Set();
    loadedFor = null;
    emit();
}

// Loads once per user. Pass a user (or null) rather than importing session.js,
// to keep the dependency pointing one way.
export async function load(user) {
    if (!user) {
        if (loadedFor !== null) reset();
        return claimed;
    }
    if (loadedFor === user.id) return claimed;

    const rows = await api.collection();
    claimed = new Set(rows.map(key));
    loadedFor = user.id;
    emit();
    return claimed;
}

// Optimistic: flip locally, fire listeners, revert and rethrow on failure.
async function mutate(poi, add) {
    const k = key(poi);
    const had = claimed.has(k);
    if (add === had) return;

    if (add) claimed.add(k); else claimed.delete(k);
    emit();

    try {
        await (add ? api.claim(poi) : api.unclaim(poi));
    } catch (error) {
        if (had) claimed.add(k); else claimed.delete(k);
        emit();
        throw error;
    }
}

export const claim = (poi) => mutate(poi, true);
export const unclaim = (poi) => mutate(poi, false);
export const toggle = (poi) => mutate(poi, !isClaimed(poi));
