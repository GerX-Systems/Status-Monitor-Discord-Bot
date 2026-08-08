# Status Monitor Discord Bot

Dieses Repository enthält einen serverseitigen Setup-CLI (Node.js / optional TypeScript) zum Erzeugen einer Konfigurationsdatei und einen kompletten Discord-Bot in Java (JDA) zur Anzeige des Status einer Statuspage.

Wichtig: Es gibt keine Web‑UI — alles läuft ausschließlich serverseitig / als Backend.

Voraussetzungen
- Node.js (empfohlen 18+) und npm (nur für das Setup‑CLI)
- Java 17+ und Maven (zum Bauen/Starten des Bots)

Schnellstart

1) Node-Abhängigkeiten installieren (nur für das CLI):

   npm install

2) Interaktives Setup ausführen (erzeugt `config.properties` und `lang/translate-example.conf` im Projekt‑Root):

   npm run setup

   Alternative CLI-Varianten:
   - npm run setup:js  (JavaScript-CLI)
   - npm run setup:ts  (TypeScript-CLI, benötigt `ts-node` oder `tsx`)

   Hinweise:
   - `config.properties.example` ist vorhanden und wird nicht überschrieben, wenn bereits vorhanden.
   - Die erzeugte `config.properties` enthält mindestens die folgenden Felder (durch CLI abgefragt):
     - `discord.bot.token` — Dein Discord-Bot-Token
     - `statuspage.name` — Subdomain der Statuspage (z. B. `example` für `example.statuspage.io`)
     - `discord.channel.incident` — Channel-ID für Incident-Nachrichten
     - `discord.channel.dashboard` — Channel-ID für das Dashboard
     - Emoji-Shortcuts, Intervall, Übersetzungsdatei & Sprache

3) Java bauen:

   mvn clean package

   Dadurch entsteht ein ausführbares Jar mit Abhängigkeiten unter `target/StatusMonitorDiscordBot-0.1.0-jar-with-dependencies.jar`.

4) Bot starten:

   java -jar target/StatusMonitorDiscordBot-0.1.0-jar-with-dependencies.jar

   - Der Bot liest `config.properties` aus dem Projekt‑Root beim Start.
   - Logausgaben erscheinen in der Konsole; prüfe, ob sich der Bot mit Discord verbindet und die Statuspage‑API erfolgreich abfragen kann.

Konfigurationsdateien
- config.properties — vom CLI erzeugt (oder manuell editierbar)
- config.properties.example — Beispielkonfiguration
- lang/translate-example.conf — Beispielübersetzungen im Format `lang.key=value` (z. B. `en.none=All systems...`)

State & Persistenz
- Laufzeitzustand (bekannte Incidents, Message‑IDs) wird in `status_state.json` im Projekt‑Root gespeichert.

Fehlerbehebung
- Wenn `discord.bot.token` fehlt oder ungültig ist, startet der Bot nicht.
- Prüfe Channel‑IDs (numeric) und ob der Bot in den entsprechenden Channels Schreibrechte hat.
- API‑Fehler der Statuspage werden in der Konsole protokolliert.

Nächste Schritte / Empfehlungen
- Optional: Validierung der CLI‑Eingaben (Token/IDs) hinzufügen.
- Optional: Single‑message‑Update für das Dashboard statt bei jedem Check neue Nachrichten zu posten (aktuelle Implementierung sendet pro Check eine Nachricht; die Speicherung/Update‑Logik kann erweitert werden).

Branch & PR
- Diese Änderungen liegen auf dem Branch `feature/setup-cli-npm` und können via Pull Request nach `develop` gemerged werden.

---

## 🚀 Start

This project runs entirely on the server (backend-only). The following steps show how to configure, build and run the bot.

Prerequisites
- Node.js (recommended v18+) and npm — only needed to run the setup CLI
- Java 17+ and Maven — required to build and run the Java bot

Quick start

1. Install Node dependencies (CLI only):

   npm install

2. Run the interactive setup to generate `config.properties` and `lang/translate-example.conf` in the repository root:

   npm run setup

   CLI Variants:
   - npm run setup:js  (JavaScript CLI)
   - npm run setup:ts  (TypeScript CLI — requires ts-node or tsx)

   The generated `config.properties` includes the following keys (prompted by the CLI):
   - `discord.bot.token` — your Discord bot token
   - `statuspage.name` — the subdomain part of the statuspage (example for `example.statuspage.io`)
   - `discord.channel.incident` — channel ID for incident messages
   - `discord.channel.dashboard` — channel ID for the dashboard
   - emoji settings, check interval, translations.file and translations.language

3. Build the Java bot (produces an executable JAR with dependencies):

   mvn clean package

   The artifact will be located at:
   `target/StatusMonitorDiscordBot-0.1.0-jar-with-dependencies.jar`

4. Start the bot:

   java -jar target/StatusMonitorDiscordBot-0.1.0-jar-with-dependencies.jar

   - The bot reads `config.properties` from the project root on startup.
   - Console logs show connection status and runtime errors.

Notes
- `lang/translate-example.conf` is provided as an example translations file (format: `lang.key=value`, e.g. `en.none=All systems are operational`).
- Runtime state (known incidents and message IDs) is stored in `status_state.json` in the project root.
- Ensure the bot token and channel IDs are correct and that the bot has write permissions in the channels configured.

Troubleshooting
- If `discord.bot.token` is missing or invalid, the bot will not start.
- Check that channel IDs are numeric and the bot user is invited to those channels.
- API or network errors are logged to the console.

If you want, I can:
- add input validation to the CLI for token/channel ID formats,
- implement single-message updating for the dashboard message (instead of sending a new message every interval),
- open a Pull Request from `feature/setup-cli-npm` into `develop` for you.
