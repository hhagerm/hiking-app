// Bootstrap: wire routes, keep the navbar in sync with the session, start.

import { router } from "./router.js";
import * as session from "./session.js";
import * as find from "./views/find.js";
import * as profile from "./views/profile.js";
import * as auth from "./views/auth.js";

const view = document.getElementById("view");
const authSlot = document.getElementById("auth-slot");

function navLink(href, text) {
    const link = document.createElement("a");
    link.href = href;
    link.textContent = text;
    link.dataset.nav = href;
    if (window.location.hash === href) link.setAttribute("aria-current", "page");
    return link;
}

function renderAuthSlot(user) {
    authSlot.replaceChildren();

    if (!user) {
        authSlot.append(navLink("#/login", "Log in"),
                        navLink("#/register", "Register"));
        return;
    }

    const logout = document.createElement("button");
    logout.type = "button";
    logout.className = "logout";
    logout.textContent = "Log out";
    logout.addEventListener("click", async () => {
        logout.disabled = true;
        try {
            await session.logout();
        } finally {
            logout.disabled = false;
            router.navigate("#/find");
        }
    });

    authSlot.append(navLink("#/profile", user.username), logout);
}

session.onChange(renderAuthSlot);

router.add("#/find", find.render);
router.add("#/profile", profile.render);
router.add("#/login", auth.renderLogin);
router.add("#/register", auth.renderRegister);
router.setFallback("#/find");

// Resolve auth state before the first render so views know who is looking.
try {
    await session.refresh();
} catch (error) {
    console.error("could not determine session state", error);
}

renderAuthSlot(session.getUser());
await router.start(view);
