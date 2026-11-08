// Login and register forms. Both map backend field errors onto the inputs.

import * as session from "../session.js";
import { router } from "../router.js";

function el(tag, props = {}, children = []) {
    const node = Object.assign(document.createElement(tag), props);
    node.append(...children);
    return node;
}

// One labelled input plus the <p> its error message goes into.
function field(name, label, type = "text", attrs = {}) {
    const input = el("input", { type, id: name, name, required: true, ...attrs });
    const error = el("p", { className: "field-error", hidden: true });
    const wrap = el("div", { className: "field" }, [
        el("label", { htmlFor: name, textContent: label }),
        input,
        error,
    ]);
    return { wrap, input, error };
}

function buildForm({ title, fields, submitLabel, hint, footer, onSubmit }) {
    const formError = el("p", { className: "form-error", hidden: true });
    const submit = el("button", { type: "submit", textContent: submitLabel });
    const form = el("form", { className: "auth" }, [
        ...fields.map((f) => f.wrap),
        ...(hint ? [el("p", { className: "muted hint", textContent: hint })] : []),
        formError,
        submit,
    ]);

    function clearErrors() {
        formError.hidden = true;
        formError.textContent = "";
        for (const f of fields) {
            f.error.hidden = true;
            f.error.textContent = "";
            f.input.removeAttribute("aria-invalid");
        }
    }

    function showErrors(apiError) {
        const remaining = { ...apiError.fieldErrors };
        for (const f of fields) {
            const message = remaining[f.input.name];
            if (message) {
                f.error.textContent = message;
                f.error.hidden = false;
                f.input.setAttribute("aria-invalid", "true");
                delete remaining[f.input.name];
            }
        }
        // Anything not tied to one of our inputs (including "_") goes up top.
        const leftovers = Object.values(remaining);
        if (leftovers.length > 0 || Object.keys(apiError.fieldErrors).length === 0) {
            formError.textContent = leftovers[0] ?? apiError.message;
            formError.hidden = false;
        }
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearErrors();
        submit.disabled = true;
        const values = Object.fromEntries(
            fields.map((f) => [f.input.name, f.input.value]),
        );
        try {
            await onSubmit(values);
            router.navigate("#/find");
        } catch (error) {
            showErrors(error);
            submit.disabled = false;
        }
    });

    return el("section", { className: "auth-page" }, [
        el("h1", { textContent: title }),
        form,
        footer,
    ]);
}

export async function renderLogin(container) {
    const fields = [
        field("username", "Username"),
        field("password", "Password", "password"),
    ];
    container.append(buildForm({
        title: "Log in",
        fields,
        submitLabel: "Log in",
        footer: el("p", { className: "muted" }, [
            document.createTextNode("No account? "),
            el("a", { href: "#/register", textContent: "Register" }),
        ]),
        onSubmit: ({ username, password }) => session.login(username, password),
    }));
}

export async function renderRegister(container) {
    const fields = [
        field("email", "Email", "email"),
        field("username", "Username", "text", { minLength: 3, maxLength: 32 }),
        field("password1", "Password", "password", { minLength: 8, maxLength: 64 }),
        field("password2", "Repeat password", "password"),
    ];
    container.append(buildForm({
        title: "Register",
        fields,
        submitLabel: "Create account",
        hint: "8-64 characters, with an uppercase letter, a lowercase letter, "
            + "a digit and a special character.",
        footer: el("p", { className: "muted" }, [
            document.createTextNode("Already registered? "),
            el("a", { href: "#/login", textContent: "Log in" }),
        ]),
        onSubmit: ({ email, username, password1, password2 }) =>
            session.register(email, username, password1, password2),
    }));
}
