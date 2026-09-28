const grid = document.getElementById("decoder-grid");
const notice = document.getElementById("notice");

const esc = value => String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

const selected = (value, expected) =>
    value === expected ? "selected" : "";

function notify(message, error = false) {
    notice.textContent = message;
    notice.className = error ? "notice visible error" : "notice visible";
    setTimeout(() => notice.className = "notice", 3000);
}

async function api(path, options = {}) {
    const response = await fetch(path, options);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Operation failed");
    }

    return data;
}

function renderDecoder(channel) {
    const disabled = channel.running ? "disabled" : "";

    return `
    <article class="card" id="decoder-card-${channel.id}">
        <div class="card-header">
            <div>
                <span class="channel-label">DECODER ${channel.id}</span>
                <input id="name-${channel.id}" class="channel-name"
                    value="${esc(channel.name)}" ${disabled}>
            </div>
            <span class="status ${channel.running ? "running" : "stopped"}">
                ${channel.running ? "RUNNING" : "STOPPED"}
            </span>
        </div>

        <div class="monitor">
            ${channel.running ? "DECODING ACTIVE" : "NO SIGNAL"}
        </div>

        <label>TIPO INGRESSO</label>
        <select id="input-type-${channel.id}" ${disabled}>
            <option value="srt"
                ${selected(channel.input_type || "srt", "srt")}>SRT</option>
            <option value="rtmp"
                ${selected(channel.input_type, "rtmp")}>RTMP / RTMPS</option>
            <option value="rtsp"
                ${selected(channel.input_type, "rtsp")}>RTSP</option>
            <option value="rtp"
                ${selected(channel.input_type, "rtp")}>RTP</option>
            <option value="udp"
                ${selected(channel.input_type, "udp")}>UDP MPEG-TS</option>
            <option value="smpte2022"
                ${selected(channel.input_type, "smpte2022")}>SMPTE 2022-2</option>
            <option value="hls"
                ${selected(channel.input_type, "hls")}>HLS / M3U8</option>
            <option value="http"
                ${selected(channel.input_type, "http")}>HTTP / HTTPS</option>
            <option value="file"
                ${selected(channel.input_type, "file")}>File locale</option>
        </select>

        <label>INDIRIZZO / PERCORSO SORGENTE</label>
        <input id="input-${channel.id}" value="${esc(channel.input_url)}"
            placeholder="https://server/channel/master.m3u8" ${disabled}>

        <label>DISPLAY MODE</label>
        <select id="display-${channel.id}" ${disabled}>
            <option value="window"
                ${selected(channel.display_mode, "window")}>Window</option>
            <option value="fullscreen"
                ${selected(channel.display_mode, "fullscreen")}>Fullscreen HDMI</option>
        </select>

        <div class="checkbox-row">
            <input type="checkbox" id="hardware-${channel.id}"
                ${channel.hardware_acceleration ? "checked" : ""}
                ${disabled}>
            <label for="hardware-${channel.id}">
                HARDWARE ACCELERATION
            </label>
        </div>

        <div class="audio-panel">
            <div class="audio-title">
                <strong>AUDIO OUTPUT</strong>
                <span id="volume-value-${channel.id}">
                    ${channel.volume ?? 100}%
                </span>
            </div>

            <input
                class="volume-slider"
                id="volume-${channel.id}"
                type="range"
                min="0"
                max="100"
                value="${channel.volume ?? 100}"
                oninput="previewVolume(${channel.id})"
                onchange="setDecoderAudio(${channel.id})"
            >

            <button
                id="mute-${channel.id}"
                class="audio-mute ${channel.muted ? "muted" : ""}"
                data-muted="${channel.muted ? "true" : "false"}"
                onclick="toggleDecoderMute(${channel.id})"
            >
                ${channel.muted ? "UNMUTE" : "MUTE"}
            </button>
        </div>

        <div class="actions">
            <button class="delete"
                onclick="deleteDecoder(${channel.id})"
                ${disabled}>DELETE</button>
            <button class="save" onclick="saveDecoder(${channel.id})"
                ${disabled}>SAVE</button>
            ${channel.running
                ? `<button class="stop"
                    onclick="stopDecoder(${channel.id})">STOP</button>`
                : `<button class="start"
                    onclick="startDecoder(${channel.id})">START</button>`}
        </div>
    </article>`;
}

async function loadDecoders() {
    try {
        const channels = await api("/api/decoders");
        grid.innerHTML = channels.map(renderDecoder).join("");
        attachAudioControls(channels);
    } catch (error) {
        notify(error.message, true);
    }
}

async function saveDecoder(id, showMessage = true) {
    const body = {
        name: document.getElementById(`name-${id}`).value,
        input_type: document.getElementById(`input-type-${id}`).value,
        input_url: document.getElementById(`input-${id}`).value,
        display_mode: document.getElementById(`display-${id}`).value,
        hardware_acceleration:
            document.getElementById(`hardware-${id}`).checked
    };

    await api(`/api/decoders/${id}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });

    if (showMessage) notify(`Decoder ${id} saved`);
}

async function startDecoder(id) {
    try {
        await saveDecoder(id, false);
        await api(`/api/decoders/${id}/start`, {method: "POST"});
        notify(`Decoder ${id} started`);
        loadDecoders();
    } catch (error) {
        notify(error.message, true);
    }
}

async function stopDecoder(id) {
    try {
        await api(`/api/decoders/${id}/stop`, {method: "POST"});
        notify(`Decoder ${id} stopped`);
        loadDecoders();
    } catch (error) {
        notify(error.message, true);
    }
}

loadDecoders();



async function createDecoder() {
    try {
        await api("/api/decoders", {method: "POST"});
        notify("New decoder input added");
        loadDecoders();
    } catch (error) {
        notify(error.message, true);
    }
}

async function deleteDecoder(id) {
    if (!confirm(`Delete Decoder ${id}?`)) return;

    try {
        await api(`/api/decoders/${id}`, {method: "DELETE"});
        notify(`Decoder ${id} deleted`);
        loadDecoders();
    } catch (error) {
        notify(error.message, true);
    }
}

function previewVolume(id) {
    const volume = document.getElementById(`volume-${id}`).value;
    document.getElementById(`volume-value-${id}`).textContent =
        `${volume}%`;
}

async function setDecoderAudio(id, mutedValue = null) {
    const slider = document.getElementById(`volume-${id}`);
    const muteButton = document.getElementById(`mute-${id}`);

    const muted = mutedValue === null
        ? muteButton.dataset.muted === "true"
        : mutedValue;

    try {
        const result = await api(`/api/decoders/${id}/audio`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                volume: Number(slider.value),
                muted: muted
            })
        });

        muteButton.dataset.muted = String(result.muted);
        muteButton.textContent = result.muted ? "UNMUTE" : "MUTE";
        muteButton.classList.toggle("muted", result.muted);
    } catch (error) {
        notify(error.message, true);
    }
}

async function toggleDecoderMute(id) {
    const button = document.getElementById(`mute-${id}`);
    const currentlyMuted = button.dataset.muted === "true";

    await setDecoderAudio(id, !currentlyMuted);
}


async function refreshDecoderStates() {
    try {
        const response = await fetch("/api/decoders");
        const channels = await response.json();

        for (const channel of channels) {
            const card = document.getElementById(
                `decoder-card-${channel.id}`
            );

            if (!card) continue;

            const status = card.querySelector(".status");
            const monitor = card.querySelector(".monitor");

            status.textContent = channel.running
                ? "RUNNING"
                : "STOPPED";

            status.className = channel.running
                ? "status running"
                : "status stopped";

            monitor.textContent = channel.running
                ? "DECODING ACTIVE"
                : "NO SIGNAL";
        }
    } catch (error) {
        console.error("Decoder status error", error);
    }
}

setInterval(refreshDecoderStates, 2000);



function attachAudioControls(channels) {
    for (const channel of channels) {
        const card = document.getElementById(
            `decoder-card-${channel.id}`
        );

        if (!card || card.querySelector(".audio-panel")) continue;

        const actions = card.querySelector(".actions");
        if (!actions) continue;

        const panel = document.createElement("div");
        panel.className = "audio-panel";

        const volume = channel.volume ?? 100;
        const muted = channel.muted ?? false;

        panel.innerHTML = `
            <div class="audio-title">
                <strong>AUDIO OUTPUT</strong>
                <span id="volume-value-${channel.id}">
                    ${volume}%
                </span>
            </div>

            <input
                class="volume-slider"
                id="volume-${channel.id}"
                type="range"
                min="0"
                max="100"
                value="${volume}"
                oninput="previewVolume(${channel.id})"
                onchange="setDecoderAudio(${channel.id})"
            >

            <button
                id="mute-${channel.id}"
                class="audio-mute ${muted ? "muted" : ""}"
                data-muted="${muted}"
                onclick="toggleDecoderMute(${channel.id})"
            >
                ${muted ? "UNMUTE" : "MUTE"}
            </button>
        `;

        actions.before(panel);
    }
}

