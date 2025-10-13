"""Application entrypoint for KlipperIWC."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from klipperiwc.api import configurator_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    app = FastAPI(
        title="KlipperIWC",
        description="Visual Klipper configuration builder",
        version="0.2.0",
    )

    app.include_router(configurator_router)

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        """Return a basic healthcheck payload."""

        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    async def configurator_ui() -> str:
        """Serve the interactive configuration builder UI."""

        return """
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>KlipperIWC – Konfigurations-Generator</title>
            <style>
                :root {
                    color-scheme: light dark;
                    font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    background: radial-gradient(circle at top, #1e293b, #0f172a);
                    color: #e2e8f0;
                }

                body {
                    margin: 0;
                    min-height: 100vh;
                    display: grid;
                    grid-template-columns: minmax(280px, 340px) 1fr;
                    gap: 0;
                }

                header {
                    grid-column: 1 / -1;
                    padding: 1.5rem 2rem 1rem;
                    border-bottom: 1px solid rgba(148, 163, 184, 0.25);
                    background: rgba(15, 23, 42, 0.85);
                    backdrop-filter: blur(12px);
                }

                header h1 {
                    margin: 0;
                    font-size: 1.9rem;
                }

                header p {
                    margin: 0.4rem 0 0;
                    color: #cbd5f5;
                }

                aside {
                    padding: 1.5rem;
                    border-right: 1px solid rgba(148, 163, 184, 0.25);
                    background: rgba(15, 23, 42, 0.75);
                    display: flex;
                    flex-direction: column;
                    gap: 1.25rem;
                }

                main {
                    padding: 1.5rem;
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }

                select, button, textarea {
                    width: 100%;
                    background: rgba(30, 41, 59, 0.85);
                    color: inherit;
                    border: 1px solid rgba(148, 163, 184, 0.35);
                    border-radius: 0.6rem;
                    padding: 0.65rem 0.8rem;
                    font-size: 1rem;
                    box-sizing: border-box;
                }

                textarea {
                    min-height: 320px;
                    font-family: "JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
                    resize: vertical;
                }

                button {
                    cursor: pointer;
                    font-weight: 600;
                    transition: transform 0.1s ease, border-color 0.2s ease;
                }

                button:hover {
                    transform: translateY(-1px);
                    border-color: #38bdf8;
                }

                fieldset {
                    border: 1px solid rgba(148, 163, 184, 0.35);
                    border-radius: 0.75rem;
                    padding: 1rem;
                }

                fieldset legend {
                    padding: 0 0.5rem;
                    font-weight: 600;
                    color: #f8fafc;
                }

                .options {
                    display: grid;
                    gap: 0.75rem;
                }

                .option-card {
                    border-radius: 0.7rem;
                    border: 1px solid rgba(148, 163, 184, 0.25);
                    padding: 0.75rem;
                    background: rgba(30, 41, 59, 0.7);
                }

                .option-card strong {
                    display: block;
                    margin-bottom: 0.35rem;
                    font-size: 1.05rem;
                }

                .tag {
                    display: inline-block;
                    padding: 0.15rem 0.5rem;
                    border-radius: 999px;
                    background: rgba(59, 130, 246, 0.2);
                    color: #93c5fd;
                    font-size: 0.75rem;
                    margin-left: 0.4rem;
                }

                .warnings {
                    border-radius: 0.7rem;
                    border: 1px solid rgba(248, 113, 113, 0.4);
                    background: rgba(248, 113, 113, 0.1);
                    color: #fecaca;
                    padding: 0.75rem;
                }

                @media (max-width: 900px) {
                    body {
                        grid-template-columns: 1fr;
                    }

                    aside {
                        border-right: none;
                        border-bottom: 1px solid rgba(148, 163, 184, 0.25);
                        flex-direction: column;
                    }
                }
            </style>
        </head>
        <body>
            <header>
                <h1>KlipperIWC Konfigurator</h1>
                <p>Erstelle Schritt für Schritt eine Klipper-Konfiguration mit der Maus.</p>
            </header>
            <aside>
                <section>
                    <label for="presetSelect">Drucker auswählen</label>
                    <select id="presetSelect"></select>
                </section>
                <section id="componentSidebar"></section>
                <button id="generateButton" type="button">Konfiguration generieren</button>
            </aside>
            <main>
                <section>
                    <fieldset>
                        <legend>Parameter-Overrides</legend>
                        <textarea id="overrides" placeholder="z.B. max_velocity: 250"></textarea>
                    </fieldset>
                </section>
                <section>
                    <fieldset>
                        <legend>Custom Macros</legend>
                        <textarea id="macros" placeholder="Gib hier eigene G-Codes oder Makros ein, jeweils durch Leerzeile getrennt."></textarea>
                    </fieldset>
                </section>
                <section>
                    <fieldset>
                        <legend>Ausgabe</legend>
                        <div id="warnings" hidden class="warnings"></div>
                        <textarea id="output" readonly placeholder="Die generierte Konfiguration erscheint hier."></textarea>
                    </fieldset>
                </section>
            </main>
            <script>
                async function loadInitialData() {
                    const [presetResponse, categoryResponse] = await Promise.all([
                        fetch('/api/configurator/presets'),
                        fetch('/api/configurator/component-groups')
                    ]);
                    if (!presetResponse.ok || !categoryResponse.ok) {
                        throw new Error('Konnte Daten nicht laden');
                    }
                    const presets = await presetResponse.json();
                    const categories = await categoryResponse.json();
                    return { presets, categories };
                }

                function renderPresets(presets, select) {
                    select.innerHTML = '';
                    for (const preset of presets) {
                        const option = document.createElement('option');
                        option.value = preset.id;
                        option.textContent = `${preset.name} – ${preset.description}`;
                        select.appendChild(option);
                    }
                }

                function renderComponentSidebar(categories, presets, container) {
                    container.innerHTML = '';
                    for (const category of categories) {
                        const wrapper = document.createElement('fieldset');
                        const legend = document.createElement('legend');
                        legend.textContent = category.label;
                        wrapper.appendChild(legend);

                        const description = document.createElement('p');
                        description.textContent = category.description;
                        description.style.marginTop = '0';
                        description.style.color = '#cbd5f5';
                        description.style.fontSize = '0.9rem';
                        description.style.marginBottom = '0.4rem';
                        wrapper.appendChild(description);

                        const select = document.createElement('select');
                        select.name = category.id;
                        for (const option of category.options) {
                            const item = document.createElement('option');
                            item.value = option.id;
                            item.textContent = option.label;
                            select.appendChild(item);
                        }
                        wrapper.appendChild(select);

                        const optionList = document.createElement('div');
                        optionList.className = 'options';
                        for (const option of category.options) {
                            const card = document.createElement('article');
                            card.className = 'option-card';
                            const header = document.createElement('strong');
                            header.textContent = option.label;
                            if (!option.config_snippet) {
                                const tag = document.createElement('span');
                                tag.className = 'tag';
                                tag.textContent = 'kein Snippet';
                                header.appendChild(tag);
                            }
                            card.appendChild(header);
                            const description = document.createElement('p');
                            description.textContent = option.description;
                            description.style.margin = '0';
                            description.style.color = '#cbd5f5';
                            description.style.fontSize = '0.85rem';
                            card.appendChild(description);
                            optionList.appendChild(card);
                        }
                        wrapper.appendChild(optionList);

                        container.appendChild(wrapper);
                    }
                }

                function parseOverrides(raw) {
                    const lines = raw.split(/\n+/).map(line => line.trim()).filter(Boolean);
                    const overrides = {};
                    for (const line of lines) {
                        const [key, ...rest] = line.split(':');
                        if (!key || rest.length === 0) continue;
                        overrides[key.trim()] = rest.join(':').trim();
                    }
                    return overrides;
                }

                function parseMacros(raw) {
                    return raw.split(/\n{2,}/).map(entry => entry.trim()).filter(Boolean);
                }

                async function generateConfiguration(presetId, components, overrides, macros) {
                    const response = await fetch('/api/configurator/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            printer_preset_id: presetId,
                            components,
                            parameter_overrides: Object.keys(overrides).length ? overrides : null,
                            custom_macros: macros.length ? macros : null,
                        }),
                    });
                    if (!response.ok) {
                        const error = await response.json().catch(() => ({}));
                        throw new Error(error.detail || 'Generierung fehlgeschlagen');
                    }
                    return response.json();
                }

                (async () => {
                    try {
                        const { presets, categories } = await loadInitialData();
                        const presetSelect = document.getElementById('presetSelect');
                        const sidebar = document.getElementById('componentSidebar');
                        const generateButton = document.getElementById('generateButton');
                        const output = document.getElementById('output');
                        const overrideTextarea = document.getElementById('overrides');
                        const macroTextarea = document.getElementById('macros');
                        const warningBox = document.getElementById('warnings');

                        renderPresets(presets, presetSelect);
                        renderComponentSidebar(categories, presets, sidebar);

                        generateButton.addEventListener('click', async () => {
                            const selectedPreset = presetSelect.value;
                            const componentSelections = {};
                            sidebar.querySelectorAll('select').forEach(select => {
                                componentSelections[select.name] = select.value;
                            });
                            const overrides = parseOverrides(overrideTextarea.value);
                            const macros = parseMacros(macroTextarea.value);

                            try {
                                const result = await generateConfiguration(selectedPreset, componentSelections, overrides, macros);
                                output.value = result.configuration;
                                if (result.warnings && result.warnings.length) {
                                    warningBox.textContent = result.warnings.join('\n');
                                    warningBox.hidden = false;
                                } else {
                                    warningBox.hidden = true;
                                    warningBox.textContent = '';
                                }
                            } catch (error) {
                                output.value = '';
                                warningBox.textContent = error.message;
                                warningBox.hidden = false;
                            }
                        });
                    } catch (error) {
                        const sidebar = document.getElementById('componentSidebar');
                        sidebar.innerHTML = `<p style="color: #fecaca;">${error.message}</p>`;
                    }
                })();
            </script>
        </body>
        </html>
        """

    return app


__all__ = ["create_app"]
