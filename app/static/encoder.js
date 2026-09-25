const grid = document.getElementById("encoder-grid");
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

function renderEncoder(channel) {
    const disabled = channel.running ? "disabled" : "";

    return `
    <article class="card">
        <div class="card-header">
            <div>
                <span class="channel-label">ENCODER ${channel.id} · NOME / ETICHETTA</span>
                <input id="name-${channel.id}" class="channel-name"
                    value="${esc(channel.name)}" ${disabled}>
            </div>
            <span class="status ${channel.running ? "running" : "stopped"}">
                ${channel.running ? "RUNNING" : "STOPPED"}
            </span>
        </div>

        <div class="monitor">
            ${channel.running ? "ENCODING ACTIVE" : "NO INPUT"}
        </div>

        <label>TIPO SORGENTE</label>
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

        <label>SORGENTE VIDEO</label>
        <input id="input-${channel.id}" value="${esc(channel.input_url)}"
            placeholder="srt://0.0.0.0:9001?mode=listener" ${disabled}>

        <label>DESTINAZIONE STREAM</label>
        <input id="output-${channel.id}" value="${esc(channel.output_url)}"
            placeholder="srt://192.168.1.100:9002" ${disabled}>

        <div class="row">
            <div>
                <label>VIDEO CODEC</label>
                <select id="video-${channel.id}" ${disabled}>
                    <option value="copy"
                        ${selected(channel.video_mode, "copy")}>Passthrough</option>
                    <option value="h264_qsv"
                        ${selected(channel.video_mode, "h264_qsv")}>H.264 QSV</option>
                    <option value="hevc_qsv"
                        ${selected(channel.video_mode, "hevc_qsv")}>H.265 QSV</option>
                    <option value="libx264"
                        ${selected(channel.video_mode, "libx264")}>H.264 CPU</option>
                    <option value="libx265"
                        ${selected(channel.video_mode, "libx265")}>H.265 CPU</option>
                </select>
            </div>

            <div>
                <label>BITRATE</label>
                <input id="bitrate-${channel.id}"
                    value="${esc(channel.video_bitrate)}"
                    placeholder="6M" ${disabled}>
            </div>
        </div>

        <label>AUDIO</label>
        <select id="audio-${channel.id}" ${disabled}>
            <option value="copy"
                ${selected(channel.audio_mode, "copy")}>Passthrough</option>
            <option value="aac"
                ${selected(channel.audio_mode, "aac")}>AAC 192 kbps</option>
        </select>

        <div class="actions">
            <button class="delete"
                onclick="deleteEncoder(${channel.id})"
                ${disabled}>DELETE</button>
            <button class="save" onclick="saveEncoder(${channel.id})"
                ${disabled}>SAVE</button>
            ${channel.running
                ? `<button class="stop"
                    onclick="stopEncoder(${channel.id})">STOP</button>`
                : `<button class="start"
                    onclick="startEncoder(${channel.id})">START</button>`}
        </div>
    </article>`;
}

async function loadEncoders() {
    try {
        const channels = await api("/api/encoders");
        grid.innerHTML = channels.map(renderEncoder).join("");
    } catch (error) {
        notify(error.message, true);
    }
}

async function saveEncoder(id, showMessage = true) {
    const body = {
        name: document.getElementById(`name-${id}`).value,
        input_type: document.getElementById(`input-type-${id}`).value,
        input_url: document.getElementById(`input-${id}`).value,
        output_url: document.getElementById(`output-${id}`).value,
        video_mode: document.getElementById(`video-${id}`).value,
        video_bitrate: document.getElementById(`bitrate-${id}`).value,
        audio_mode: document.getElementById(`audio-${id}`).value
    };

    await api(`/api/encoders/${id}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });

    if (showMessage) notify(`Encoder ${id} saved`);
}

async function startEncoder(id) {
    try {
        await saveEncoder(id, false);
        await api(`/api/encoders/${id}/start`, {method: "POST"});
        notify(`Encoder ${id} started`);
        loadEncoders();
    } catch (error) {
        notify(error.message, true);
    }
}

async function stopEncoder(id) {
    try {
        await api(`/api/encoders/${id}/stop`, {method: "POST"});
        notify(`Encoder ${id} stopped`);
        loadEncoders();
    } catch (error) {
        notify(error.message, true);
    }
}

loadEncoders();



async function createEncoder() {
    try {
        await api("/api/encoders", {method: "POST"});
        notify("New encoder input added");
        loadEncoders();
    } catch (error) {
        notify(error.message, true);
    }
}

async function deleteEncoder(id) {
    if (!confirm(`Delete Encoder ${id}?`)) return;

    try {
        await api(`/api/encoders/${id}`, {method: "DELETE"});
        notify(`Encoder ${id} deleted`);
        loadEncoders();
    } catch (error) {
        notify(error.message, true);
    }
}
