(function () {
    "use strict";

    const root = document.documentElement;
    let deferredInstallPrompt = null;

    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        deferredInstallPrompt = event;
        document.getElementById("installAppButton")?.classList.add("install-ready");
    });

    function csrfToken() {
        const cookie = document.cookie
            .split("; ")
            .find((item) => item.startsWith("csrftoken="));
        return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
    }

    function showToast(message) {
        const toast = document.getElementById("appToast");
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add("show");
        window.clearTimeout(showToast.timer);
        showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 2800);
    }

    function setupTheme() {
        const button = document.getElementById("themeToggle");
        if (!button) return;
        const update = () => {
            const dark = root.dataset.theme === "dark";
            button.querySelector("i").className = dark
                ? "bi bi-sun-fill"
                : "bi bi-moon-stars-fill";
            button.querySelector(".theme-label").textContent = dark ? "Light" : "Dark";
            button.setAttribute(
                "aria-label",
                dark ? "Switch to light theme" : "Switch to dark theme"
            );
        };
        update();
        button.addEventListener("click", () => {
            const next = root.dataset.theme === "dark" ? "light" : "dark";
            root.dataset.theme = next;
            try {
                localStorage.setItem("swiftcart-theme", next);
            } catch (error) {
                // The theme still works when storage is unavailable.
            }
            update();
        });
    }

    function setupAlerts() {
        document.querySelectorAll(".alert").forEach((alert) => {
            window.setTimeout(() => {
                if (window.bootstrap) {
                    bootstrap.Alert.getOrCreateInstance(alert).close();
                }
            }, 4500);
        });
    }

    function setupCountdown() {
        const sale = document.querySelector(".flash-sale-section");
        if (!sale) return;
        const end = new Date(sale.dataset.saleEnd).getTime();
        const hours = document.getElementById("countHours");
        const minutes = document.getElementById("countMinutes");
        const seconds = document.getElementById("countSeconds");
        const tick = () => {
            let remaining = Math.max(0, end - Date.now());
            const hourValue = Math.floor(remaining / 3600000);
            remaining %= 3600000;
            const minuteValue = Math.floor(remaining / 60000);
            const secondValue = Math.floor((remaining % 60000) / 1000);
            hours.textContent = String(hourValue).padStart(2, "0");
            minutes.textContent = String(minuteValue).padStart(2, "0");
            seconds.textContent = String(secondValue).padStart(2, "0");
        };
        tick();
        window.setInterval(tick, 1000);
    }

    function notificationElement(item) {
        const wrapper = document.createElement(item.url ? "a" : "div");
        wrapper.className = `notification-item ${item.is_read ? "" : "unread"}`;
        if (item.url) wrapper.href = item.url;
        const icon = document.createElement("i");
        icon.className = `bi ${item.icon}`;
        const content = document.createElement("div");
        const title = document.createElement("strong");
        const message = document.createElement("p");
        const time = document.createElement("small");
        title.textContent = item.title;
        message.textContent = item.message;
        time.textContent = item.created_at;
        content.append(title, message, time);
        wrapper.append(icon, content);
        return wrapper;
    }

    function setupNotifications() {
        const button = document.getElementById("notificationButton");
        const list = document.getElementById("notificationList");
        const badge = document.getElementById("notificationBadge");
        if (!button || !list || !badge) return;
        let previousCount = Number(badge.textContent || 0);

        const load = async (renderList = false) => {
            try {
                const response = await fetch("/api/notifications/", {
                    headers: { Accept: "application/json" },
                });
                if (!response.ok) return;
                const data = await response.json();
                badge.textContent = data.count;
                badge.hidden = data.count === 0;
                if (data.count > previousCount && previousCount !== 0) {
                    showToast("You have a new SwiftCart notification.");
                }
                previousCount = data.count;
                if (renderList) {
                    list.replaceChildren();
                    if (!data.items.length) {
                        const empty = document.createElement("div");
                        empty.className = "notification-empty";
                        empty.textContent = "You are all caught up.";
                        list.append(empty);
                    } else {
                        data.items.forEach((item) => list.append(notificationElement(item)));
                    }
                }
            } catch (error) {
                if (renderList) list.textContent = "Unable to load alerts.";
            }
        };

        button.addEventListener("click", () => load(true));
        document
            .getElementById("markNotificationsRead")
            ?.addEventListener("click", async () => {
                await fetch("/api/notifications/read/", {
                    method: "POST",
                    headers: { "X-CSRFToken": csrfToken() },
                });
                badge.hidden = true;
                badge.textContent = "0";
                list.querySelectorAll(".unread").forEach((item) => {
                    item.classList.remove("unread");
                });
            });
        window.setInterval(() => load(false), 15000);
    }

    function setupWishlist() {
        document.addEventListener("submit", async (event) => {
            const form = event.target.closest(".js-wishlist-form");
            if (!form) return;
            event.preventDefault();
            const button = form.querySelector("button");
            button.disabled = true;
            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    headers: {
                        "X-CSRFToken": csrfToken(),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.message || "Wishlist update failed.");
                document
                    .querySelectorAll(
                        `.js-wishlist-form[data-product-id="${form.dataset.productId}"]`
                    )
                    .forEach((matchingForm) => {
                        const matchingButton = matchingForm.querySelector("button");
                        const icon = matchingButton.querySelector("i");
                        matchingButton.classList.toggle("active", data.active);
                        matchingButton.setAttribute("aria-pressed", String(data.active));
                        icon.className = data.active ? "bi bi-heart-fill" : "bi bi-heart";
                        const label = matchingButton.querySelector("[data-wishlist-label]");
                        if (label) {
                            label.textContent = data.active
                                ? "Remove from wishlist"
                                : "Add to wishlist";
                        }
                        matchingButton.classList.add("wishlist-pop");
                        window.setTimeout(
                            () => matchingButton.classList.remove("wishlist-pop"),
                            450
                        );
                    });
                const badge = document.getElementById("wishlistNavBadge");
                if (badge) {
                    badge.textContent = data.count;
                    badge.hidden = data.count === 0;
                }
                showToast(data.message);
            } catch (error) {
                showToast(error.message || "Could not update wishlist.");
            } finally {
                button.disabled = false;
            }
        });
    }

    function setupChat() {
        const shell = document.querySelector(".support-chat");
        const toggle = document.getElementById("chatToggle");
        const close = document.getElementById("chatClose");
        const windowElement = document.getElementById("chatWindow");
        const messages = document.getElementById("chatMessages");
        const form = document.getElementById("chatForm");
        const input = document.getElementById("chatInput");
        if (!shell || !toggle || !windowElement || !messages || !form || !input) return;
        const endpoint = shell.dataset.chatEndpoint;
        let pollTimer = null;

        const render = (items) => {
            messages.replaceChildren();
            items.forEach((item) => {
                const bubble = document.createElement("div");
                bubble.className =
                    item.sender === "customer"
                        ? "user-message"
                        : item.sender === "agent"
                          ? "agent-message"
                          : "bot-message";
                const body = document.createElement("span");
                const time = document.createElement("small");
                body.textContent = item.body;
                time.textContent = `${item.sender_label} · ${item.created_at}`;
                bubble.append(body, time);
                messages.append(bubble);
            });
            messages.scrollTop = messages.scrollHeight;
        };

        const load = async () => {
            try {
                const response = await fetch(endpoint, {
                    headers: { Accept: "application/json" },
                });
                if (response.ok) render((await response.json()).messages);
            } catch (error) {
                // Poll again after a transient connection failure.
            }
        };

        const open = () => {
            windowElement.classList.add("open");
            load();
            window.clearInterval(pollTimer);
            pollTimer = window.setInterval(load, 4000);
            window.setTimeout(() => input.focus(), 120);
        };
        const hide = () => {
            windowElement.classList.remove("open");
            window.clearInterval(pollTimer);
        };
        toggle.addEventListener("click", () =>
            windowElement.classList.contains("open") ? hide() : open()
        );
        close.addEventListener("click", hide);

        const send = async (message) => {
            if (!message.trim()) return;
            const body = new URLSearchParams({ message: message.trim() });
            input.disabled = true;
            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "X-CSRFToken": csrfToken(),
                        Accept: "application/json",
                    },
                    body,
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || "Unable to send message.");
                render(data.messages);
                input.value = "";
            } catch (error) {
                showToast(error.message);
            } finally {
                input.disabled = false;
                input.focus();
            }
        };
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            send(input.value);
        });
        document.querySelectorAll("[data-chat]").forEach((button) => {
            button.addEventListener("click", () => send(button.dataset.chat));
        });
    }

    function setupPayment() {
        const cards = document.querySelectorAll("[data-payment-card]");
        const upiPanel = document.getElementById("upiPaymentPanel");
        const copyButton = document.getElementById("copyUpiButton");
        const upiText = document.getElementById("upiIdText");
        if (!cards.length) return;
        const update = () => {
            cards.forEach((card) => {
                const radio = card.querySelector('input[type="radio"]');
                card.classList.toggle("active", Boolean(radio?.checked));
            });
            const selected = document.querySelector(
                'input[name="payment_method"]:checked'
            );
            if (upiPanel) upiPanel.hidden = selected?.value !== "upi";
        };
        cards.forEach((card) => {
            card.addEventListener("click", () => {
                const radio = card.querySelector('input[type="radio"]');
                if (radio) radio.checked = true;
                update();
            });
        });
        copyButton?.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(upiText.textContent.trim());
                showToast("UPI ID copied.");
            } catch (error) {
                window.prompt("Copy this UPI ID:", upiText.textContent.trim());
            }
        });
        update();
    }

    function setupReveal() {
        const nodes = document.querySelectorAll(".reveal-on-scroll");
        if (!("IntersectionObserver" in window)) {
            nodes.forEach((node) => node.classList.add("is-visible"));
            return;
        }
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.08 }
        );
        nodes.forEach((node, index) => {
            node.style.transitionDelay = `${Math.min(index % 4, 3) * 70}ms`;
            observer.observe(node);
        });
    }

    function setupCatalogueFilters() {
        const toggle = document.getElementById("mobileFilterToggle");
        const panel = document.getElementById("catalogueFilterPanel");
        if (!toggle || !panel) return;
        toggle.addEventListener("click", () => {
            const open = !panel.classList.contains("is-open");
            panel.classList.toggle("is-open", open);
            toggle.setAttribute("aria-expanded", String(open));
        });
    }

    function setupPwa() {
        const installButton = document.getElementById("installAppButton");
        const installModalElement = document.getElementById("installHelpModal");
        const installMessage = document.getElementById("installHelpMessage");
        const installSteps = document.getElementById("installHelpSteps");
        const isInstalled = () =>
            window.matchMedia("(display-mode: standalone)").matches ||
            window.navigator.standalone === true;

        const openInstallHelp = () => {
            const isMac = /Mac/.test(navigator.platform);
            const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome|CriOS/.test(navigator.userAgent);
            if (installMessage && installSteps && isMac && isSafari) {
                installMessage.textContent = "Safari can add SwiftCart directly to your Mac Dock.";
                installSteps.innerHTML = '<div><span>1</span><p>Open the <strong>File</strong> menu.</p></div><div><span>2</span><p>Select <strong>Add to Dock</strong>.</p></div><div><span>3</span><p>Confirm the SwiftCart app name.</p></div>';
            }
            if (window.bootstrap && installModalElement) {
                bootstrap.Modal.getOrCreateInstance(installModalElement).show();
            } else {
                window.alert("Open your browser menu and choose Install SwiftCart or Add to Dock.");
            }
        };

        const updateButton = () => {
            if (!installButton) return;
            const label = installButton.querySelector("span");
            const icon = installButton.querySelector("i");
            if (isInstalled()) {
                installButton.classList.add("app-installed");
                label.textContent = "Installed";
                icon.className = "bi bi-check2-circle";
            } else {
                installButton.classList.remove("app-installed");
                label.textContent = "Install App";
                icon.className = "bi bi-phone";
            }
        };

        updateButton();
        if ("serviceWorker" in navigator) {
            window.addEventListener("load", () => {
                navigator.serviceWorker
                    .register("/service-worker.js", { updateViaCache: "none" })
                    .then((registration) => registration.update())
                    .catch(() => {});
            });
            let refreshing = false;
            navigator.serviceWorker.addEventListener("controllerchange", () => {
                if (refreshing) return;
                refreshing = true;
                window.location.reload();
            });
        }
        installButton?.addEventListener("click", async () => {
            if (isInstalled()) {
                showToast("SwiftCart is already installed on this device.");
                return;
            }
            if (!deferredInstallPrompt) {
                openInstallHelp();
                return;
            }
            deferredInstallPrompt.prompt();
            const choice = await deferredInstallPrompt.userChoice;
            deferredInstallPrompt = null;
            installButton.classList.remove("install-ready");
            if (choice.outcome === "accepted") {
                showToast("Installing SwiftCart...");
            } else {
                showToast("Installation was cancelled. You can try again anytime.");
                openInstallHelp();
            }
        });
        window.addEventListener("appinstalled", () => {
            deferredInstallPrompt = null;
            updateButton();
            showToast("SwiftCart installed successfully.");
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        setupTheme();
        setupAlerts();
        setupCountdown();
        setupNotifications();
        setupWishlist();
        setupChat();
        setupPayment();
        setupReveal();
        setupCatalogueFilters();
        setupPwa();
    });

    window.addEventListener("load", () => {
        window.setTimeout(
            () => document.getElementById("pageLoader")?.classList.add("is-hidden"),
            180
        );
    });
})();
