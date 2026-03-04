self.addEventListener("push", function (event) {
    if (!event.data) return;

    const data = event.data.json();

    const title = data.title || "Yangi xabar";
    const options = {
        body: data.body || "",
        icon: data.icon || "/static/images/favicon.png",
        badge: data.icon || "/static/images/favicon.png",
        data: { url: data.url || "/" },
        vibrate: [200, 100, 200],
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", function (event) {
    event.notification.close();
    const url = event.notification.data?.url || "/";

    event.waitUntil(
        clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
            for (const client of clientList) {
                if (client.url === url && "focus" in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) return clients.openWindow(url);
        })
    );
});