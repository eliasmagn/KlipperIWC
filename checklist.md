# Aufgabenliste

## Erledigt

- [x] Basis-FastAPI-Anwendung initialisieren
- [x] Deploy-Skripte für Produktion und Entwicklung bereitstellen
- [x] Docker-Image für containerisierte Ausführung definieren
- [x] SQLAlchemy-Grundkonfiguration mit erster Alembic-Migration einrichten

## Offene Schritte Richtung Produktivbetrieb

- [ ] API-Spezifikation und Pydantic-Modelle für Druckerstatus, Temperaturen und aktive Jobs erstellen
- [ ] Klipper-Polling-Client bzw. Event-Receiver implementieren und als Service-Layer kapseln
- [ ] Persistente Statushistorie via SQLite mit Service-Layer und Retention-Strategie aufbauen
- [ ] Websocket-Gateway zur Verteilung der Status-Updates an UI-Clients entwickeln
- [ ] Dashboard-Layout im Webfrontend mit Navigation und Grundseiten strukturieren
- [ ] Live-Widgets für Temperaturkurven und Jobfortschritt mit Websocket-Daten verknüpfen
- [ ] JSON-Schema für Board-Definitionen finalisieren und Versionsverwaltung im Repository etablieren
- [ ] Upload-Workflow für Board-Grafiken samt S3-/Dateisystem-Storage und Moderationsschritt implementieren
- [ ] Validierungslogik für Pin-Namen gegen MCU-Datenbank ergänzen und mit Unit-Tests absichern
- [ ] CI/CD-Pipeline mit Linting, Tests und automatischem Container-Build & Tagging aufsetzen
