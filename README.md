<div align="center">
  <img src="https://res.cloudinary.com/btzjbj3t/image/upload/v1785670990/Status_Monitor_Discord_Bot_1_hqiuhp.png" alt="Banner" width="100%" style="max-width: 1200px; border-radius: 10px;">
</div>
<br>
<br>
<div align="center">

[![GerX-Systems](https://badgen.net/static/%20/Powered%20by%20GerX%20Systems/000f80?icon=https://res.cloudinary.com/btzjbj3t/image/upload/v1783619426/gerx-systems-icon_1_eveneb.svg)](https://github.com/GerX-Systems)
</div>
<br>
<div align="center">
  
![Version](https://badgen.net/github/tag/Gerx-Systems/Status-Monitor-Discord-Bot)
![Releases](https://badgen.net/github/release/GerX-Systems/Status-Monitor-Discord-Bot)
![Stars](https://badgen.net/github/stars/GerX-Systems/Status-Monitor-Discord-Bot)


</div>
<div align="center">

[![Discord](https://badgen.net/badge/%20/Discord/blue?icon=discord)](https://discord.gg/C4u5Qf3sN5)
[![Website](https://badgen.net/badge/🌐%20/Website/blue)](https://gerx-systems.de)
[![GitHub Org](https://badgen.net/static/org/GerX%20Systems/blue)](https://github.com/GerX-Systems)
[![Customer Support](https://badgen.net/static/%20/E-Mail/blue?icon=maildotru)](mailto:suppot@gerx-systems.de)
</div>
<br>
<br>
<div align="center">
<h1>Welcome!</h1>
<p><strong>NOTICE:</strong> A status page on <a href="https://statuspage.io/">statuspage.io</a> is required.</p><p><strong>AI:</strong> Parts of the code were created/edited using AI.</p>
</div>
<br><br>

## 📑 Table of Contents

- [About](#about)
- [🚀 Start](#-start)
- [Prerequisites](#prerequisites)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Translations (lang/)](#translations-lang)
- [CLI](#cli)
- [Build & Run (Java)](#build--run-java)
- [State & Persistence](#state--persistence)
- [Troubleshooting](#troubleshooting)
- [Contributing & Branches](#contributing--branches)
- [Contact](#contact)

---

## About

This repository provides a server-only Status Monitor Discord Bot. It includes:

- An interactive setup CLI (Node.js / optional TypeScript) to generate configuration and initial translation files.
- A Java-based Discord bot (JDA) that polls a Statuspage.io summary endpoint and posts updates to Discord channels.

There is no web UI — this project runs entirely on the backend.

## 🚀 Start

This project runs entirely on the server (backend-only). The following steps show how to prepare, build and run the bot in the recommended order.

### Prerequisites
- Node.js (recommended v18+) and npm — only needed to run the setup CLI
- Java 17+ and Maven — required to build and run the Java bot
- pm2 (optional) — recommended to run the long‑running processes in production

### Recommended Startup Sequence

Follow this order on your server:

1. Install Node dependencies (CLI + helpers):

   npm install

2. Build the project (compile TS, bundle assets, prepare Node scripts):

   npm run build

   - This builds the CLI (if TypeScript is used) and prepares any Node-side artifacts. Ensure your package.json contains a `build` script.

3. Start the background process manager (pm2) and run the bot/JVM there.

   Example 1 — start the Java JAR with pm2:

   pm2 start --name status-monitor --interpreter none -- java -jar target/StatusMonitorDiscordBot-0.1.0-jar-with-dependencies.jar

   Example 2 — start via npm script (if `start` is defined):

   pm2 start npm --name status-monitor -- run start

   Example 3 — using an ecosystem file (recommended for production):

   pm2 start ecosystem.config.js --env production

4. Run the interactive setup CLI (this writes config.properties and creates language files under `lang/`):

   npm run setup

   Important: The setup CLI used here is the same CLI used for the Open Ticket functionality — it will prompt for language selection (dropdown), tokens, channel IDs, emojis, and write `translations.file` and `translations.language` into `config.properties`.

5. (If necessary) Restart the pm2 process so the bot picks up the newly created config.properties:

   pm2 restart status-monitor

Notes
- The reason the CLI runs after starting pm2 is to allow the daemon/main process to be managed (and restarted) by pm2; you can run the CLI locally or via SSH on the server. After writing `config.properties`, a restart ensures the running bot loads the configuration.
- If you prefer to run the setup locally and then push config.properties to the server, you can do that too — the key is that the running process must have access to the final `config.properties` and `lang/` files.

## Configuration

The CLI will generate `config.properties`. Important keys:

- `discord.bot.token` — your Discord bot token (required)
- `statuspage.name` — statuspage subdomain (e.g. `example` for `example.statuspage.io`)
- `discord.channel.incident` — numeric Channel ID for incident messages
- `discord.channel.dashboard` — numeric Channel ID for the dashboard
- `emoji.*` — emojis for status indicators (operational, degraded_performance, partial_outage, major_outage, maintenance)
- `check.interval.seconds` — polling interval in seconds (default 300)
- `translations.file` — path to a translation file (e.g. `lang/de.json` or `lang/de.conf`)
- `translations.language` — language code (e.g. `de`)

Example (created by the CLI):

```properties
discord.bot.token=YOUR_DISCORD_BOT_TOKEN
statuspage.name=YOUR_STATUSPAGE_NAME
discord.channel.incident=123456789012345678
discord.channel.dashboard=234567890123456789
check.interval.seconds=300
translations.file=lang/eng.json
translations.language=en
```

## Translations (lang/)

All user-facing texts (embed titles, descriptions, field labels, buttons, dashboard text) are translatable via files in the `lang/` directory.

Supported formats:
- JSON (recommended): `lang/<lang>.json` — e.g. `lang/eng.json` — { "key": "text" }
- CONF / properties: `lang/<lang>.conf` or `.properties` — `key=value` or `key="value"`

Files included in this repo under `lang/`:
- `lang/eng.json` — full English reference (key → English text)
- `lang/translate-example.json` — JSON example template you can copy for new languages

How to add a new language:
1. Copy `lang/translate-example.json` to `lang/de.json` (or create `lang/de.conf`).
2. Replace the values with translations; do not change the keys.
3. Keep placeholders unchanged (e.g. `{page}`, `{name}`, `{time}`).
4. Use the CLI to select the translation file or set `translations.file` and `translations.language` in `config.properties`.

Fallback order: JSON → conf/properties → legacy language-prefixed properties → capitalized key fallback.

## CLI

Two CLIs are provided:

- JS/TS CLI (recommended)
  - Uses Inquirer to prompt for values and lists detected `lang/` files in a dropdown.
  - Creates `lang/` and default files if missing.
  - Run: `npm install` → `npm run setup`.

- Java CLI
  - Interactive CLI that lists detected `lang/` files and accepts a numeric selection.
  - Useful if you prefer a pure-Java setup.

Both CLIs write `config.properties` and create initial language files when necessary.

## Build & Run (Java)

Build:

```
mvn clean package
```

Run:

```
java -jar target/StatusMonitorDiscordBot-0.1.0-jar-with-dependencies.jar
```

The bot will:
- Load `config.properties` from the project root
- Connect to Discord with the provided token
- Poll Statuspage.io `summary.json` and post updates to the configured channels

## State & Persistence

Runtime state (known incidents, message IDs, indicator state) is stored in `status_state.json` in the project root so the bot avoids reposting duplicate updates.

## Troubleshooting

- Bot won’t start / login fails: Check `discord.bot.token` and ensure the token is valid.
- No messages in channel: Verify the channel IDs are numeric and that the bot has write permissions.
- Translations not applied: Ensure `translations.file` points to the correct file and that the keys exist.
- Statuspage API errors: Check network access and the `statuspage.name` value.

## Contributing & Branches

- Work is currently on the branch `feature/setup-cli-npm`.
- If you want, I can open a Pull Request into `develop` with these changes.

## Contact

- GitHub: https://github.com/GerX-Systems
- Website: https://gerx-systems.de
- Discord: https://discord.gg/C4u5Qf3sN5
- Support: suppot@gerx-systems.de

---

If you want, I can:
- create a `lang/de.json` draft in the branch,
- add a preview command to the CLI to render an example embed with the chosen language,
- or open a PR from `feature/setup-cli-npm` to `develop`.
