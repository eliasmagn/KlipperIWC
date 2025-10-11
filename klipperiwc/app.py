"""Application entrypoint for KlipperIWC."""

from __future__ import annotations

import os
from functools import lru_cache

from fastapi import FastAPI
from fastapi.responses import HTMLResponse


@lru_cache(maxsize=1)
def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(title="KlipperIWC", description="Klipper Integration Web Console")

    @app.get("/")
    async def healthcheck() -> dict[str, str]:
        """Return a basic healthcheck payload."""
        return {"status": "ok"}

    @app.get("/board-designer", response_class=HTMLResponse)
    async def board_designer() -> str:
        """Return an interactive board designer prototype page."""

        return """
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
            <meta charset=\"utf-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <title>KlipperIWC – Board Designer</title>
            <style>
                :root {
                    color-scheme: light dark;
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
                    background: #111827;
                    color: #f9fafb;
                }

                body {
                    margin: 0;
                    min-height: 100vh;
                    display: grid;
                    grid-template-columns: minmax(260px, 320px) 1fr;
                    background: #0f172a;
                }

                header {
                    grid-column: 1 / -1;
                    padding: 1.5rem 2rem 1rem;
                    border-bottom: 1px solid rgba(148, 163, 184, 0.3);
                    background: rgba(15, 23, 42, 0.9);
                    backdrop-filter: blur(12px);
                }

                header h1 {
                    margin: 0;
                    font-size: 1.8rem;
                }

                header p {
                    margin: 0.3rem 0 0;
                    color: #cbd5f5;
                    font-size: 0.95rem;
                }

                aside {
                    padding: 1.5rem;
                    border-right: 1px solid rgba(148, 163, 184, 0.3);
                    background: rgba(15, 23, 42, 0.85);
                    backdrop-filter: blur(14px);
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }

                main {
                    padding: 1.5rem;
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                }

                .toolbar {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.6rem;
                }

                button, select, input {
                    background: rgba(30, 41, 59, 0.8);
                    color: #e2e8f0;
                    border: 1px solid rgba(148, 163, 184, 0.4);
                    border-radius: 0.45rem;
                    padding: 0.5rem 0.9rem;
                    font-size: 0.95rem;
                    cursor: pointer;
                    transition: transform 0.1s ease, border-color 0.2s ease;
                }

                button.active {
                    border-color: #38bdf8;
                    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25);
                }

                button:hover, select:hover {
                    transform: translateY(-1px);
                    border-color: #38bdf8;
                }

                .canvas-shell {
                    flex: 1;
                    min-height: 60vh;
                    border-radius: 0.75rem;
                    border: 1px solid rgba(148, 163, 184, 0.3);
                    background: radial-gradient(circle at top, rgba(148, 163, 184, 0.08), rgba(15, 23, 42, 0.9));
                    position: relative;
                    overflow: hidden;
                }

                svg {
                    width: 100%;
                    height: 100%;
                    display: block;
                    background: repeating-linear-gradient(0deg, rgba(148, 163, 184, 0.08) 0, rgba(148, 163, 184, 0.08) 1px, transparent 1px, transparent 32px),
                        repeating-linear-gradient(90deg, rgba(148, 163, 184, 0.08) 0, rgba(148, 163, 184, 0.08) 1px, transparent 1px, transparent 32px);
                }

                .shape-label {
                    fill: #f1f5f9;
                    font-size: 13px;
                    text-shadow: 0 1px 2px rgba(15, 23, 42, 0.8);
                    pointer-events: none;
                }

                .shape-entry {
                    border-radius: 0.6rem;
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    padding: 0.75rem;
                    background: rgba(30, 41, 59, 0.65);
                }

                .shape-entry h3 {
                    margin: 0 0 0.25rem;
                    font-size: 1rem;
                    color: #e2e8f0;
                }

                .shape-entry p {
                    margin: 0;
                    color: #cbd5f5;
                    font-size: 0.85rem;
                }

                .hint {
                    font-size: 0.85rem;
                    color: #94a3b8;
                    margin-top: -0.3rem;
                }

                @media (max-width: 900px) {
                    body {
                        display: flex;
                        flex-direction: column;
                    }

                    aside {
                        border-right: none;
                        border-bottom: 1px solid rgba(148, 163, 184, 0.3);
                        flex-direction: row;
                        flex-wrap: wrap;
                        gap: 1rem;
                    }

                    .shape-entry {
                        flex: 1 1 200px;
                    }
                }
            </style>
        </head>
        <body>
            <header>
                <h1>Board Designer Prototype</h1>
                <p>Create annotated board overlays before the user-generated workflow is available.</p>
            </header>
            <aside>
                <div>
                    <h2>Workflow</h2>
                    <p class=\"hint\">Select a tool, drag on the canvas, then name the connector/pin.</p>
                    <div class=\"toolbar\">
                        <button id=\"rectTool\" type=\"button\">Rectangle</button>
                        <button id=\"circleTool\" type=\"button\">Circle</button>
                        <button id=\"panTool\" type=\"button\">Pan</button>
                        <input type=\"color\" id=\"colorPicker\" value=\"#38bdf8\" title=\"Highlight color\" />
                    </div>
                </div>
                <section>
                    <h2>Annotated Pins</h2>
                    <div id=\"shapeList\"></div>
                </section>
            </aside>
            <main>
                <div class=\"canvas-shell\">
                    <svg id=\"boardCanvas\" viewBox=\"0 0 1280 720\" role=\"img\" aria-label=\"Board designer canvas\"></svg>
                </div>
            </main>

            <script>
                const boardCanvas = document.getElementById('boardCanvas');
                const rectTool = document.getElementById('rectTool');
                const circleTool = document.getElementById('circleTool');
                const panTool = document.getElementById('panTool');
                const colorPicker = document.getElementById('colorPicker');
                const shapeList = document.getElementById('shapeList');

                let activeTool = null;
                let drawing = false;
                let startPoint = { x: 0, y: 0 };
                let currentShape = null;
                let currentLabel = null;
                let viewBox = { x: 0, y: 0, width: 1280, height: 720 };
                let panStart = null;

                function setActiveTool(tool) {
                    activeTool = tool;
                    for (const button of [rectTool, circleTool, panTool]) {
                        button.classList.toggle('active', button.dataset.tool === tool);
                    }
                    boardCanvas.style.cursor = tool === 'pan' ? 'grab' : 'crosshair';
                }

                function svgCursor(event) {
                    const point = boardCanvas.createSVGPoint();
                    point.x = event.offsetX;
                    point.y = event.offsetY;
                    const ctm = boardCanvas.getScreenCTM();
                    if (!ctm) {
                        return null;
                    }
                    return point.matrixTransform(ctm.inverse());
                }

                function addShapeEntry(id, type, label, color, geometry) {
                    const wrapper = document.createElement('article');
                    wrapper.className = 'shape-entry';
                    wrapper.innerHTML = `
                        <h3>${label}</h3>
                        <p><strong>Type:</strong> ${type}</p>
                        <p><strong>Color:</strong> ${color}</p>
                        <p><strong>Geometry:</strong> ${geometry}</p>
                    `;
                    wrapper.dataset.shapeId = id;
                    shapeList.appendChild(wrapper);
                }

                function promptForLabel(defaultValue) {
                    const result = prompt('Pin / connector label', defaultValue ?? '');
                    if (!result) {
                        return null;
                    }
                    return result.trim();
                }

                function createLabelElement(x, y, text) {
                    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    label.setAttribute('x', x);
                    label.setAttribute('y', y);
                    label.setAttribute('class', 'shape-label');
                    label.textContent = text;
                    return label;
                }

                function createShapeId() {
                    return `shape-${Math.random().toString(36).slice(2, 9)}`;
                }

                rectTool.dataset.tool = 'rect';
                circleTool.dataset.tool = 'circle';
                panTool.dataset.tool = 'pan';

                [rectTool, circleTool, panTool].forEach((button) => {
                    button.addEventListener('click', () => {
                        setActiveTool(button.dataset.tool);
                    });
                });

                setActiveTool('rect');

                boardCanvas.addEventListener('mousedown', (event) => {
                    const cursorPoint = svgCursor(event);
                    if (!cursorPoint) {
                        return;
                    }

                    if (activeTool === 'pan') {
                        panStart = { x: cursorPoint.x, y: cursorPoint.y, viewBox: { ...viewBox } };
                        boardCanvas.style.cursor = 'grabbing';
                        return;
                    }

                    drawing = true;
                    startPoint = { x: cursorPoint.x, y: cursorPoint.y };

                    const color = colorPicker.value;

                    if (activeTool === 'rect') {
                        currentShape = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                        currentShape.setAttribute('x', startPoint.x);
                        currentShape.setAttribute('y', startPoint.y);
                        currentShape.setAttribute('width', 1);
                        currentShape.setAttribute('height', 1);
                        currentShape.setAttribute('rx', 6);
                        currentShape.setAttribute('fill', `${color}33`);
                        currentShape.setAttribute('stroke', color);
                        currentShape.setAttribute('stroke-width', 2);
                        boardCanvas.appendChild(currentShape);
                    } else if (activeTool === 'circle') {
                        currentShape = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                        currentShape.setAttribute('cx', startPoint.x);
                        currentShape.setAttribute('cy', startPoint.y);
                        currentShape.setAttribute('r', 1);
                        currentShape.setAttribute('fill', `${color}33`);
                        currentShape.setAttribute('stroke', color);
                        currentShape.setAttribute('stroke-width', 2);
                        boardCanvas.appendChild(currentShape);
                    }
                });

                boardCanvas.addEventListener('mousemove', (event) => {
                    const cursorPoint = svgCursor(event);
                    if (!cursorPoint) {
                        return;
                    }

                    if (panStart && activeTool === 'pan') {
                        const dx = cursorPoint.x - panStart.x;
                        const dy = cursorPoint.y - panStart.y;

                        viewBox.x = panStart.viewBox.x - dx;
                        viewBox.y = panStart.viewBox.y - dy;
                        boardCanvas.setAttribute('viewBox', `${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`);
                        return;
                    }

                    if (!drawing || !currentShape) {
                        return;
                    }

                    const updatedPoint = cursorPoint;

                    if (activeTool === 'rect') {
                        const width = updatedPoint.x - startPoint.x;
                        const height = updatedPoint.y - startPoint.y;
                        currentShape.setAttribute('x', Math.min(startPoint.x, updatedPoint.x));
                        currentShape.setAttribute('y', Math.min(startPoint.y, updatedPoint.y));
                        currentShape.setAttribute('width', Math.abs(width));
                        currentShape.setAttribute('height', Math.abs(height));
                    } else if (activeTool === 'circle') {
                        const dx = updatedPoint.x - startPoint.x;
                        const dy = updatedPoint.y - startPoint.y;
                        const radius = Math.sqrt(dx * dx + dy * dy);
                        currentShape.setAttribute('r', radius);
                    }
                });

                window.addEventListener('mouseup', () => {
                    if (panStart) {
                        panStart = null;
                        boardCanvas.style.cursor = 'grab';
                        return;
                    }

                    if (!drawing || !currentShape) {
                        return;
                    }

                    drawing = false;

                    const color = colorPicker.value;
                    const shapeId = createShapeId();
                    currentShape.dataset.shapeId = shapeId;

                    if (activeTool === 'rect') {
                        const width = parseFloat(currentShape.getAttribute('width'));
                        const height = parseFloat(currentShape.getAttribute('height'));
                        if (width < 10 || height < 10) {
                            currentShape.remove();
                            currentShape = null;
                            return;
                        }
                    } else if (activeTool === 'circle') {
                        const radius = parseFloat(currentShape.getAttribute('r'));
                        if (radius < 8) {
                            currentShape.remove();
                            currentShape = null;
                            return;
                        }
                    }

                    const labelText = promptForLabel();
                    if (!labelText) {
                        currentShape.remove();
                        currentShape = null;
                        return;
                    }

                    let labelElement;
                    if (activeTool === 'rect') {
                        const x = parseFloat(currentShape.getAttribute('x'));
                        const y = parseFloat(currentShape.getAttribute('y'));
                        const width = parseFloat(currentShape.getAttribute('width'));
                        const height = parseFloat(currentShape.getAttribute('height'));
                        labelElement = createLabelElement(x + width / 2, y + height / 2, labelText);
                        labelElement.setAttribute('text-anchor', 'middle');
                        labelElement.setAttribute('dominant-baseline', 'middle');
                        boardCanvas.appendChild(labelElement);
                        addShapeEntry(
                            shapeId,
                            'Rectangle',
                            labelText,
                            color,
                            `x:${x.toFixed(1)}, y:${y.toFixed(1)}, w:${width.toFixed(1)}, h:${height.toFixed(1)}`
                        );
                    } else if (activeTool === 'circle') {
                        const cx = parseFloat(currentShape.getAttribute('cx'));
                        const cy = parseFloat(currentShape.getAttribute('cy'));
                        const radius = parseFloat(currentShape.getAttribute('r'));
                        labelElement = createLabelElement(cx, cy, labelText);
                        labelElement.setAttribute('text-anchor', 'middle');
                        labelElement.setAttribute('dominant-baseline', 'middle');
                        boardCanvas.appendChild(labelElement);
                        addShapeEntry(
                            shapeId,
                            'Circle',
                            labelText,
                            color,
                            `cx:${cx.toFixed(1)}, cy:${cy.toFixed(1)}, r:${radius.toFixed(1)}`
                        );
                    }

                    currentLabel = labelElement;
                    currentShape = null;
                });
            </script>
        </body>
        </html>
        """

    return app


def main() -> None:
    """Launch the ASGI server using uvicorn."""
    import uvicorn

    app_env = os.getenv("APP_ENV", "development")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = app_env != "production"

    uvicorn.run(
        "klipperiwc.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
        log_level=os.getenv("LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
