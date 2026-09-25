const grid = document.getElementById("channels");
const notification = document.getElementById("notification");

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function selected(current, expected) {
    return current === expected ? "selected" : "";
}

function notify(message, error = false) {
    notification.textContent = message;
    notification.className = error
        ? "notification visible error"
        : "notification visible";

    setTimeout(() => {
        notification.className = "notification";
    }, 3500);
}

async function request(path, options = {}) {
    const response = await fetch(path, options);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Operation failed");
    }

    return data;
}

function channelCard(channel) {
    const statusClass = channel.running ? "running" : "stopped";
    const statusText = channel.running ? "RUNNING" : "STOPPED";

    return `
        <article class="channel-card" id="channel-${channel.id}">
            <div class="channel-header">
                <div>
                    <span class="channel-number">CHANNEL ${channel.id}</span>
                    <input
                        id="name-${channel.id}"
                        class="channel-name"
                        value="${escapeHtml(channel.name)}"
                    >
                </div>

                <span class="status ${statusClass}">
                    ${statusText}
                </span>
            </div>

            <div class="preview">
                <span>${channel.running ? "STREAM ACTIVE" : "NO SIGNAL"}</span>
            </div>

            <label>INPUT URL</label>
            <input
                id="input-${channel.id}"
                placeholder="srt://0.0.0.0:9001?mode=listener"
                value="${escapeHtml(channel.input_url)}"
                ${channel.running ? "disabled" : ""}
            >

            <label>OUTPUT URL</label>
            <input
                id="output-${channel.id}"
                placeholder="udp://239.10.10.1:5000"
                value="${escapeHtml(channel.output_url)}"
                ${channel.running ? "disabled" : ""}
            >

            <div class="settings-grid">
                <div>
                    <label>VIDEO MODE</label>
                    <select
                        id="video-${channel.id}"
                        ${channel.running ? "disabled" : ""}
                    >
                        <option value="copy"
                            ${selected(channel.video_mode, "copy")}>
                            Passthrough
                        </option>
                        <option value="h264_qsv"
                            ${selected(channel.video_mode, "h264_qsv")}>
                            H.264 Intel QSV
                        </option>
                        <option value="hevc_qsv"
                            ${selected(channel.video_mode, "hevc_qsv")}>
                            H.265 Intel QSV
                        </option>
                        <option value="libx264"
                            ${selected(channel.video_mode, "libx264")}>
                            H.264 CPU
                        </option>
                        <option value="libx265"
                            ${selected(channel.video_mode, "libx265")}>
                            H.265 CPU
                        </option>
                    </select>
                </div>

                <div>
                    <label>AUDIO MODE</label>
                    <select
                        id="audio-${channel.id}"
                        ${channel.running ? "disabled" : ""}
                    >
                        <option value="copy"
                            ${selected(channel.audio_mode, "copy")}>
                            Passthrough
                        </option>
                        <option value="aac"
                            ${selected(channel.audio_mode, "aac")}>
                            AAC
                        </option>
                    </select>
                </div>
            </div>

            <div class="actions">
                <button
                    class="save-button"
                    onclick="saveChannel(${channel.id})"
                    ${channel.running ? "disabled" : ""}
                >
                    SAVE
                </button>

                ${
                    channel.running
                    ? `<button class="stop-button"
                         onclick="stopChannel(${channel.id})">STOP</button>`
                    : `<button class="start-button"
                         onclick="startChannel(${channel.id})">START</button>`
                }
            </div>
        </article>
    `;
}

async function loadChannels() {
    try {
        const channels = await request("/api/channels");
        grid.innerHTML = channels.map(channelCard).join("");
    } catch (error) {
        notify(error.message, true);
    }
}

async function saveChannel(channelId, showMessage = true) {
    const configuration = {
        name: document.getElementById(`name-${channelId}`).value,
        input_url: document.getElementById(`input-${channelId}`).value,
        output_url: document.getElementById(`output-${channelId}`).value,
        video_mode: document.getElementById(`video-${channelId}`).value,
        audio_mode: document.getElementById(`audio-${channelId}`).value
    };

    await request(`/api/channels/${channelId}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(configuration)
    });

    if (showMessage) {
        notify(`Channel ${channelId} saved`);
    }
}

async function startChannel(channelId) {
    try {
        await saveChannel(channelId, false);
        await request(`/api/channels/${channelId}/start`, {
            method: "POST"
        });

        notify(`Channel ${channelId} started`);
        await loadChannels();
    } catch (error) {
        notify(error.message, true);
    }
}

async function stopChannel(channelId) {
    try {
        await request(`/api/channels/${channelId}/stop`, {
            method: "POST"
        });

        notify(`Channel ${channelId} stopped`);
        await loadChannels();
    } catch (error) {
        notify(error.message, true);
    }
}

loadChannels();

setInterval(() => {
    const activeElement = document.activeElement?.tagName;

    if (activeElement !== "INPUT" && activeElement !== "SELECT") {
        loadChannels();
    }
}, 3000);
