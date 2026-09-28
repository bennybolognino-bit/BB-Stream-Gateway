const viewer = document.getElementById("webrtc-viewer");
const stage = document.getElementById("webrtc-stage");
const labels = document.getElementById("channel-labels");
const statusElement = document.getElementById("multiview-status");
const waitingMessage = document.getElementById("waiting-message");
const message = document.getElementById("multiview-message");
const layoutSelector = document.getElementById("layout-selector");
const customColumns = document.getElementById("custom-columns");
const channelOrder = document.getElementById("channel-order");

let viewerAttached = false;
let draggedItem = null;

async function api(path, options = {}) {
    const response = await fetch(path, options);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Operation failed");
    }

    return data;
}

function layoutChanged() {
    customColumns.style.display =
        layoutSelector.value === "custom"
            ? "block"
            : "none";

    savePreset();
}

function savePreset() {
    localStorage.setItem(
        "bb-multiview-layout",
        layoutSelector.value
    );

    localStorage.setItem(
        "bb-multiview-columns",
        customColumns.value
    );

    localStorage.setItem(
        "bb-multiview-order",
        JSON.stringify(getChannelOrder())
    );
}

function loadPreset() {
    layoutSelector.value =
        localStorage.getItem("bb-multiview-layout")
        || "grid2";

    customColumns.value =
        localStorage.getItem("bb-multiview-columns")
        || "2";

    layoutChanged();
}

function getChannelOrder() {
    return [...channelOrder.querySelectorAll(".order-item")]
        .map(item => Number(item.dataset.channelId));
}

function renderChannelOrder(channels) {
    const saved = JSON.parse(
        localStorage.getItem("bb-multiview-order")
        || "[]"
    );

    const lookup = new Map(
        channels.map(channel => [channel.id, channel])
    );

    const ordered = [];

    for (const id of saved) {
        if (lookup.has(id)) {
            ordered.push(lookup.get(id));
            lookup.delete(id);
        }
    }

    ordered.push(...lookup.values());

    channelOrder.innerHTML = ordered.map(channel => `
        <div
            class="order-item"
            draggable="true"
            data-channel-id="${channel.id}">
            <span class="drag-handle">â˜°</span>
            <strong>${channel.name}</strong>
            <span>Decoder ${channel.id}</span>
        </div>
    `).join("");

    enableDragging();
}

function enableDragging() {
    const items = channelOrder.querySelectorAll(".order-item");

    items.forEach(item => {
        item.addEventListener("dragstart", () => {
            draggedItem = item;
            item.classList.add("dragging");
        });

        item.addEventListener("dragend", () => {
            item.classList.remove("dragging");
            draggedItem = null;
            savePreset();
        });

        item.addEventListener("dragover", event => {
            event.preventDefault();

            if (!draggedItem || draggedItem === item) return;

            const rectangle = item.getBoundingClientRect();
            const after =
                event.clientY >
                rectangle.top + rectangle.height / 2;

            channelOrder.insertBefore(
                draggedItem,
                after ? item.nextSibling : item
            );
        });
    });
}

async function loadChannels() {
    try {
        const channels = await api("/api/decoders");

        renderChannelOrder(
            channels.filter(channel =>
                channel.input_url?.trim()
            )
        );
    } catch (error) {
        message.textContent = error.message;
    }
}

function renderLabels(state) {
    labels.className = "channel-labels";
    labels.innerHTML = "";

    for (const tile of state.tiles) {
        const overlay = document.createElement("div");
        overlay.className = "channel-overlay";
        overlay.textContent = tile.id
            ? `CH ${tile.id} Â· ${tile.name}`
            : "NO SIGNAL";

        overlay.style.left =
            `${tile.x / 12.8}%`;

        overlay.style.top =
            `${tile.y / 7.2}%`;

        overlay.style.width =
            `${tile.width / 12.8}%`;

        overlay.style.height =
            `${tile.height / 7.2}%`;

        labels.appendChild(overlay);
    }
}

function applyStatus(state) {
    statusElement.textContent =
        state.running ? "ON AIR" : "STOPPED";

    statusElement.className =
        state.running ? "status running" : "status stopped";

    if (state.running) {
        layoutSelector.value = state.layout;
        customColumns.value = state.custom_columns;
        layoutChanged();
        renderLabels(state);
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
        labels.innerHTML = "";
    }
}

async function startMultiview() {
    message.textContent = "Starting multiview...";
    savePreset();

    try {
        const state = await api("/api/multiview/start", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                layout: layoutSelector.value,
                custom_columns: Number(customColumns.value),
                channel_ids: getChannelOrder()
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
    stage.requestFullscreen?.();
}

async function refreshStatus() {
    try {
        const state = await api("/api/multiview/status");
        applyStatus(state);
    } catch (error) {
        console.error(error);
    }
}

loadPreset();
loadChannels();
refreshStatus();
setInterval(refreshStatus, 3000);
