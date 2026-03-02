(() => {
    function wsUrl(path) {
        const proto = window.location.protocol === "https:" ? "wss" : "ws";
        return `${proto}://${window.location.host}${path}`;
    }

    let socket;
    let pingTimer;
    let reconnectTimer;

    function startPing() {
        clearInterval(pingTimer);
        pingTimer = setInterval(() => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({type: "ping"}));
            }
        }, 25000);
    }

    function stopPing() {
        clearInterval(pingTimer);
    }

    function connect() {
        socket = new WebSocket(wsUrl("/ws/inbox/"));

        socket.onopen = () => startPing();

        socket.onclose = () => {
            stopPing();
            clearTimeout(reconnectTimer);
            reconnectTimer = setTimeout(connect, 1200);
        };

        socket.onerror = () => {
            try {
                socket.close();
            } catch {
            }
        };
    }

    connect();
})();