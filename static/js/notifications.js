lucide?.createIcons?.();

const notifSocket = new WebSocket((location.protocol === "https:" ? "wss" : "ws") + "://" + location.host + "/ws/notifications/");

notifSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);

    if (data.type === "new_message_notification") {
        const currentChatUsername = window.CHAT?.receiverUsername;
        if (currentChatUsername && currentChatUsername === data.sender_username) {
            return;
        }
        showInAppNotification(data);
    }
};

notifSocket.onclose = function () {
    setTimeout(() => location.reload(), 3000);
};

function injectNotifStyles() {
    if (document.getElementById("__notif-styles")) return;

    const style = document.createElement("style");
    style.id = "__notif-styles";
    style.textContent = `
.notif-container {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 99999;
    display: flex;
    flex-direction: column;
    gap: .75rem;
    pointer-events: none;
}
@media (max-width: 640px) {
    .notif-container {
        left: 50%;
        right: auto;
        transform: translateX(-50%);
        width: min(92vw, 420px);
    }
}
.notif-toast {
    pointer-events: auto;
    width: min(380px, 92vw);
    border-radius: 1.25rem;
    border: 1px solid rgba(59,130,246,.25);
    background: rgba(255,255,255,.92);
    backdrop-filter: blur(10px);
    box-shadow: 0 18px 40px rgba(0,0,0,.12);
    overflow: hidden;
    display: grid;
    grid-template-columns: 48px 1fr 36px;
    align-items: center;
    gap: .5rem;
    padding: .75rem .9rem;
    cursor: pointer;
    opacity: 0;
    transform: translateX(28px) scale(.98);
    transition: transform .28s ease, opacity .28s ease;
}
.notif-toast--in  { opacity: 1; transform: translateX(0) scale(1); }
.notif-toast--out { opacity: 0; transform: translateX(28px) scale(.98); }
.notif-toast__avatar {
    width: 40px; height: 40px;
    border-radius: 50%;
    object-fit: cover;
}
.notif-toast__avatar-placeholder {
    width: 40px; height: 40px;
    border-radius: 50%;
    background: rgb(59,130,246);
    display: grid;
    place-items: center;
    color: #fff;
    font-weight: 700;
    font-size: 1.1rem;
}
.notif-toast__close {
    width: 32px; height: 32px;
    border-radius: 10px;
    display: grid;
    place-items: center;
    background: transparent;
    border: none;
    cursor: pointer;
    color: rgba(15,23,42,.5);
    transition: background .15s ease, color .15s ease;
}
.notif-toast__close:hover {
    background: rgba(0,0,0,.06);
    color: rgba(15,23,42,.9);
}
.notif-toast__bar {
    position: absolute;
    left: 0; bottom: 0;
    height: 3px; width: 100%;
    transform-origin: left;
    transform: scaleX(1);
    background: rgb(59,130,246);
    opacity: .55;
}
@keyframes notifBar {
    from { transform: scaleX(1); }
    to   { transform: scaleX(0); }
}
    `;
    document.head.appendChild(style);
}

function getNotifContainer() {
    let c = document.getElementById("__notif-container");
    if (!c) {
        c = document.createElement("div");
        c.id = "__notif-container";
        c.className = "notif-container";
        document.body.appendChild(c);
    }
    return c;
}

function showInAppNotification({sender_name, sender_avatar, message_preview, chat_url}) {
    injectNotifStyles();

    const container = getNotifContainer();
    const DURATION = 5000;

    const toast = document.createElement("div");
    toast.className = "notif-toast";

    const avatarHTML = sender_avatar ? `<img src="${sender_avatar}" class="notif-toast__avatar" />` : `<div class="notif-toast__avatar-placeholder">${sender_name[0].toUpperCase()}</div>`;

    toast.innerHTML = `
        ${avatarHTML}
        <div style="min-width:0">
            <p style="font-size:.875rem;font-weight:600;color:rgba(15,23,42,.92);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${sender_name}</p>
            <p style="font-size:.75rem;color:rgba(15,23,42,.55);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:1px;">${message_preview}</p>
        </div>
        <button class="notif-toast__close" type="button"><i data-lucide="x" style="width:14px;height:14px;"></i></button>
        <div class="notif-toast__bar"></div>
    `;

    container.appendChild(toast);
    lucide?.createIcons?.();

    requestAnimationFrame(() => toast.classList.add("notif-toast--in"));

    const bar = toast.querySelector(".notif-toast__bar");
    const closeBtn = toast.querySelector(".notif-toast__close");

    let timer = null;
    let remaining = DURATION;
    let start = performance.now();
    let paused = false;

    const remove = () => {
        toast.classList.remove("notif-toast--in");
        toast.classList.add("notif-toast--out");
        clearTimeout(timer);
        setTimeout(() => toast.remove(), 280);
    };

    const startTimer = () => {
        paused = false;
        start = performance.now();
        bar.style.animation = "none";
        void bar.offsetHeight;
        bar.style.animation = `notifBar linear ${remaining}ms forwards`;
        clearTimeout(timer);
        timer = setTimeout(remove, remaining);
    };

    const pauseTimer = () => {
        if (paused) return;
        paused = true;
        remaining = Math.max(0, remaining - (performance.now() - start));
        clearTimeout(timer);
        const matrix = getComputedStyle(bar).transform;
        bar.style.animation = "none";
        bar.style.transform = matrix === "none" ? "scaleX(1)" : matrix;
    };

    closeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        remove();
    });
    toast.addEventListener("mouseenter", pauseTimer);
    toast.addEventListener("mouseleave", startTimer);
    toast.addEventListener("click", () => {
        window.location.href = chat_url;
    });

    startTimer();
    showBrowserNotification(sender_name, message_preview, chat_url);
}

async function requestNotificationPermission() {
    if (!("Notification" in window)) return;
    if (Notification.permission === "granted") {
        await registerPush();
        return;
    }
    if (Notification.permission === "denied") {
        showNotifBlockedBanner();
        return;
    }

    const permission = await Notification.requestPermission();
    if (permission === "granted") {
        await registerPush();
    } else if (permission === "denied") {
        showNotifBlockedBanner();
    }
}

async function registerPush() {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) return;

    try {
        const reg = await navigator.serviceWorker.register("/service-worker.js");
        await navigator.serviceWorker.ready;

        let subscription = await reg.pushManager.getSubscription();

        if (!subscription) {
            const res = await fetch("/push/vapid-public-key/");
            const {vapid_public_key} = await res.json();

            subscription = await reg.pushManager.subscribe({
                userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(vapid_public_key),
            });
        }

        await fetch("/push/subscribe/", {
            method: "POST", headers: {
                "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken"),
            }, body: JSON.stringify(subscription),
        });

    } catch (err) {
        console.error("Push registration xatolik:", err);
    }
}

async function showBrowserNotification(title, body, url) {
    if (Notification.permission !== "granted") return;
    if (document.hasFocus()) return;

    try {
        const reg = await navigator.serviceWorker.ready;
        await reg.showNotification(title, {
            body: body,
            icon: "/static/images/favicon.png",
            badge: "/static/images/favicon.png",
            data: { url: url },
            vibrate: [200, 100, 200],
        });
    } catch (err) {
        console.error("SW notification xatolik:", err);
    }
}

function showNotifBlockedBanner() {
    if (document.getElementById("__notif-blocked-banner")) return;

    const banner = document.createElement("div");
    banner.id = "__notif-blocked-banner";
    banner.className = ["fixed bottom-5 left-1/2 -translate-x-1/2 z-[9999]", "bg-yellow-50 dark:bg-zinc-800", "border border-yellow-300 dark:border-zinc-600", "rounded-2xl shadow-xl", "flex items-center gap-3", "px-4 py-3 max-w-sm w-full",].join(" ");

    banner.innerHTML = `
        <i data-lucide="bell-off" class="w-5 h-5 text-yellow-500 flex-shrink-0"></i>
        <p class="text-xs text-gray-700 dark:text-gray-300 flex-1">
            Bildirishnomalar bloklangan. Ruxsat berish uchun
            <strong><i data-lucide="lock" class="inline w-3 h-3"></i> &rarr; Sayt sozlamalari &rarr; Bildirishnomalar &rarr; Ruxsat</strong>
        </p>
        <button id="__notif-blocked-close" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 leading-none transition-colors">
            <i data-lucide="x" class="w-4 h-4"></i>
        </button>
    `;

    banner.querySelector("#__notif-blocked-close").onclick = () => banner.remove();
    document.body.appendChild(banner);
    lucide?.createIcons?.();

    setTimeout(() => banner?.remove(), 10000);
}

function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const rawData = atob(base64);
    return new Uint8Array([...rawData].map((c) => c.charCodeAt(0)));
}

function getCookie(name) {
    for (const cookie of document.cookie.split(";")) {
        const [k, v] = cookie.trim().split("=");
        if (k === name) return decodeURIComponent(v);
    }
    return "";
}

document.addEventListener("DOMContentLoaded", () => {
    requestNotificationPermission();
});