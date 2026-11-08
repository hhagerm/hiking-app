// Owns "who is logged in". Nothing else may cache the current user.

import { api, ApiError } from "./api.js";
import * as claims from "./claims.js";

let user = null;
const listeners = new Set();

function emit() {
    for (const fn of listeners) fn(user);
}

export function getUser() {
    return user;
}

export function isLoggedIn() {
    return user !== null;
}

// Returns an unsubscribe function.
export function onChange(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
}

function setUser(next) {
    user = next;
    claims.reset();      // claimed set belongs to whoever was logged in
    emit();
    return user;
}

// Called once on page load. 401 means no session; 404/405 means /user/me isn't
// implemented on the backend yet - both are "anonymous", not an error.
export async function refresh() {
    try {
        return setUser(await api.me());
    } catch (error) {
        if (error instanceof ApiError && [401, 404, 405].includes(error.status)) {
            return setUser(null);
        }
        throw error;
    }
}

export async function login(username, password) {
    return setUser(await api.login(username, password));
}

// The backend's register does not create a session, so log in straight after
// with the credentials the user just typed.
export async function register(email, username, password1, password2) {
    await api.register(email, username, password1, password2);
    return login(username, password1);
}

// Half-real until the backend grows DELETE /user/session: see docs/frontend.md.
// The cookie is httponly, so a hard refresh will restore the session.
export async function logout() {
    try {
        await api.logout();
    } catch (error) {
        const notImplemented =
            error instanceof ApiError && [404, 405].includes(error.status);
        if (!notImplemented) throw error;
    } finally {
        setUser(null);
    }
}
