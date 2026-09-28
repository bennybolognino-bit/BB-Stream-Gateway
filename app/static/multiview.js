const viewer = document.getElementById("webrtc-viewer");
const stage = document.getElementById("webrtc-stage");
const labels = document.getElementById("channel-labels");
const statusElement = document.getElementById("multiview-status");
const waitingMessage = document.getElementById("waiting-message");
const message = document.getElementById("multiview-message");
const layoutSelector = document.getElementById("layout-selector");

let viewerAttached = false;

async function api(path, options = {}) {
    const response = await fetch(path, options);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Operation failed");
    }

    return data;
}

function renderLabels(state) {
    const slots = state.layout * state.layout;

    labels.className =
        `channel-labels layout-${state.layout}`;

    const items = [];

    for (let index = 0; index < slots; index++) {
        const channel = state.channels[index];

        items.push(`
            <div class="channel-overlay">
                ${channel
                    ? `CH ${channel.id} · ${channel.name}`
                    : "NO SIGNAL"}
            </div>
        `);
    }

    labels.innerHTML = items.join("");
}

function applyStatus(state) {
    statusElement.textContent =
        state.running ? "ON AIR" : "STOPPED";

    statusElement.className =
        state.running ? "status running" : "status stopped";

    layoutSelector.value = String(state.layout);
    renderLabels(state);

    if (state.running) {
        waitingMessage.style.display = "none";

        if (!viewerAttached) {
            setTimeout(() => {
                viewer.src =
                    `${state.webrtc_url}` +
                    `?controls=false` +
                    `&muted=true` +
                    `&autoplay=true` +
                    `&playsInline=true` +
                    `&t=${Date.now()}`;

                viewerAttached = true;
            }, 1200);
        }
    } else {
        viewer.src = "about:blank";
        viewerAttached = false;
        waitingMessage.style.display = "grid";
    }
}

async function startMultiview() {
    message.textContent = "Starting WebRTC multiview...";

    try {
        const state = await api("/api/multiview/start", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                layout: Number(layoutSelector.value)
            })
        });

        viewerAttached = false;
        applyStatus(state);
        message.textContent = "Multiview started";
    } catch (error) {
        message.textContent = error.message;
    }
}

async function stopMultiview() {
    try {
        const state = await api("/api/multiview/stop", {
            method: "POST"
        });

        applyStatus(state);
        message.textContent = "Multiview stopped";
    } catch (error) {
        message.textContent = error.message;
    }
}

function openFullscreen() {
    if (stage.requestFullscreen) {
        stage.requestFullscreen();
    }
}

async function refreshStatus() {
    try {
        const state = await api("/api/multiview/status");
        applyStatus(state);
    } catch (error) {
        console.error(error);
    }
}

refreshStatus();
setInterval(refreshStatus, 3000);
