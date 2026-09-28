const grid = document.getElementById("multiview-grid");
const layoutSelector = document.getElementById("layout");

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
}

function changeLayout() {
    grid.className =
        `multiview-grid layout-${layoutSelector.value}`;

    localStorage.setItem(
        "multiview-layout",
        layoutSelector.value
    );
}

function renderTile(channel) {
    const configured = Boolean(channel.input_url?.trim());
    const timestamp = Date.now();

    return `
        <article class="multiview-tile">
            <div class="tile-header">
                <strong>${escapeHtml(channel.name)}</strong>
                <span class="${configured ? "configured" : "offline"}">
                    ${configured ? "READY" : "NO INPUT"}
                </span>
            </div>

            <div class="tile-video">
                ${configured
                    ? `<img
                        src="/api/multiview/preview/${channel.id}?t=${timestamp}"
                        alt="${escapeHtml(channel.name)}"
                        onerror="this.classList.add('preview-error')"
                       >`
                    : `<div class="no-signal">NO SIGNAL</div>`
                }
            </div>

            <div class="tile-footer">
                <span>DECODER ${channel.id}</span>
                <a href="/decoder">CONFIGURE</a>
            </div>
        </article>
    `;
}

async function loadMultiview() {
    try {
        const response = await fetch("/api/decoders");

        if (!response.ok) {
            throw new Error("Unable to load decoders");
        }

        const channels = await response.json();
        grid.innerHTML = channels.map(renderTile).join("");
    } catch (error) {
        grid.innerHTML = `
            <div class="multiview-error">
                ${escapeHtml(error.message)}
            </div>
        `;
    }
}

const savedLayout =
    localStorage.getItem("multiview-layout") || "2";

layoutSelector.value = savedLayout;
changeLayout();
loadMultiview();
