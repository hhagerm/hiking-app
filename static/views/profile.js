// Account info plus the claimed POIs. Auth-only.

import { api } from "../api.js";
import * as session from "../session.js";
import * as claims from "../claims.js";
import { router } from "../router.js";

function el(tag, props = {}, children = []) {
    const node = Object.assign(document.createElement(tag), props);
    node.append(...children);
    return node;
}

function formatDate(iso) {
    const date = new Date(iso);
    return Number.isNaN(date.valueOf())
        ? iso
        : date.toLocaleDateString(undefined,
            { year: "numeric", month: "short", day: "numeric" });
}

export async function render(container) {
    const user = session.getUser();
    if (!user) {
        router.navigate("#/login");
        return;
    }

    const count = el("span", { textContent: "..." });
    container.append(
        el("h1", { textContent: user.username }),
        el("dl", { className: "account" }, [
            el("dt", { textContent: "Email" }),
            el("dd", { textContent: user.email }),
            el("dt", { textContent: "Member since" }),
            el("dd", { textContent: formatDate(user.create_ts) }),
            el("dt", { textContent: "Peaks claimed" }),
            el("dd", {}, [count]),
        ]),
        el("h2", { textContent: "Claimed peaks" }),
    );

    const status = el("p", { className: "status", textContent: "Loading..." });
    const list = el("ul", { className: "collection" });
    container.append(status, list);

    // claims.js owns the key set; the full rows (name, elevation, timestamp)
    // are only needed here, so this view fetches them itself on each mount.
    let rows;
    try {
        rows = await api.collection();
    } catch (error) {
        status.textContent = `Failed to load your collection: ${error.message}`;
        status.classList.add("error");
        return;
    }

    const EMPTY = "Nothing claimed yet - go find a peak.";

    count.textContent = String(rows.length);
    if (rows.length === 0) {
        status.textContent = EMPTY;
        return;
    }
    status.hidden = true;

    for (const poi of rows) {
        const button = el("button", {
            type: "button", className: "unclaim", textContent: "Remove",
        });
        const item = el("li", {}, [
            el("div", { className: "collection-main" }, [
                el("strong", { textContent: poi.name ?? "(unnamed)" }),
                el("span", {
                    className: "muted",
                    textContent: poi.ele_m === null ? "" : ` ${poi.ele_m} m`,
                }),
            ]),
            el("div", { className: "muted" }, [
                el("span", { textContent: `Claimed ${formatDate(poi.collect_ts)}` }),
            ]),
            button,
        ]);

        button.addEventListener("click", async () => {
            button.disabled = true;
            try {
                await claims.unclaim(poi);
                item.remove();
                count.textContent = String(claims.count());
                if (list.children.length === 0) {
                    status.hidden = false;
                    status.textContent = EMPTY;
                }
            } catch (error) {
                button.disabled = false;
                status.hidden = false;
                status.classList.add("error");
                status.textContent = `Could not remove that: ${error.message}`;
            }
        });

        list.append(item);
    }

    // Keep the set in sync so the find view paints correctly on return.
    await claims.load(user);
    count.textContent = String(claims.count());
}
