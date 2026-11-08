// Minimal hash router. Views are `render(container)` functions that may return
// a cleanup function, called before the next view mounts.

const routes = new Map();
let container = null;
let fallback = null;
let cleanup = null;

function pathFromHash() {
    const hash = window.location.hash;
    return routes.has(hash) ? hash : fallback;
}

function markActiveLinks(path) {
    for (const link of document.querySelectorAll("[data-nav]")) {
        if (link.dataset.nav === path) {
            link.setAttribute("aria-current", "page");
        } else {
            link.removeAttribute("aria-current");
        }
    }
}

async function show() {
    const path = pathFromHash();
    const render = routes.get(path);
    if (!render) return;

    if (cleanup) {
        cleanup();
        cleanup = null;
    }
    container.replaceChildren();
    markActiveLinks(path);

    const result = await render(container);
    cleanup = typeof result === "function" ? result : null;
}

export const router = {
    add(path, render) {
        routes.set(path, render);
    },

    setFallback(path) {
        fallback = path;
    },

    start(el) {
        container = el;
        window.addEventListener("hashchange", () => void show());
        return show();
    },

    navigate(path) {
        if (window.location.hash === path) {
            void show();                 // same route: re-render in place
        } else {
            window.location.hash = path;  // triggers hashchange
        }
    },

    // Re-run the current view, e.g. after login changes what it should show.
    reload() {
        return show();
    },
};
