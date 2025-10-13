# Roadmap

## Phase 1 – Konfigurationsbasis (abgeschlossen)
- [x] FastAPI-Dienst mit Konfigurationsendpunkten aufsetzen
- [x] Browser-UI für Preset- und Komponenten-Auswahl bereitstellen
- [x] Presets, Komponenten und Generator-Logik modellieren
- [x] Automatisierte Tests und Deploy-Skripte aktualisieren

## Phase 2 – Komfortfunktionen (aktuell)
- [ ] Download der generierten `printer.cfg` anbieten
- [ ] Auswahlzustand im Browser speichern (LocalStorage)
- [ ] Kontextuelle Hilfetexte und Tooltips pro Komponente ergänzen
- [ ] Validierung der Parameter-Overrides mit Fehlermeldungen

## Phase 3 – Preset-Erweiterung
- [ ] Weitere Drucker-Presets (Prusa, RatRig, Voron V0, etc.) hinterlegen
- [ ] Komponentenbibliothek um Treiber, Sensoren und Heizbett-Varianten erweitern
- [ ] Struktur für Community-Beiträge definieren (Vorlagen, Contribution-Guide)

## Phase 4 – Zusammenarbeit & Export
- [ ] Teilen von Konfigurationen via URL-Parameter oder JSON-Export ermöglichen
- [ ] Import-Funktion für bestehende `printer.cfg` (Analyse der Sektionen)
- [ ] Export als ZIP mit `printer.cfg` und zusätzlicher Dokumentation

## Phase 5 – Integrationen
- [ ] Optionale Anbindung an Klipper-Instanzen zur direkten Übertragung prüfen
- [ ] Plug-in-Schnittstelle für Hersteller-spezifische Komponenten entwerfen
- [ ] Telemetrie über anonyme Nutzungsstatistiken (opt-in) evaluieren
