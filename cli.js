import inquirer from "inquirer";
import fs from "fs/promises";
import path from "path";

const TRANSLATIONS_EXAMPLE = `# Example translations file
# Format: <lang>.<key>=<translation>

en.none=All systems are operational
en.minor=Minor restriction
en.major=Major outage
en.critical=Critical failure
en.maintenance=Maintenance work
en.investigating=Will be examined
en.identified=Cause identified
en.monitoring=It is being observed.
en.resolved=Fixed
en.operational=Operational
en.degraded_performance=Limited performance
en.partial_outage=Partial failure
en.major_outage=Severe failure
en.under_maintenance=Maintenance work

de.none=Alle Systeme betriebsbereit
de.minor=Kleinere Einschränkung
de.major=Großer Ausfall
de.critical=Kritischer Fehler
de.maintenance=Wartungsarbeiten
de.investigating=Es wird untersucht
de.identified=Ursache identifiziert
de.monitoring=Es wird beobachtet.
de.resolved=Behoben
de.operational=Betriebsbereit
de.degraded_performance=Eingeschränkte Leistung
de.partial_outage=Teilweiser Ausfall
de.major_outage=Schwerer Ausfall
de.under_maintenance=Wartungsarbeiten
`;

const CONFIG_EXAMPLE = `# Example config.properties (created by CLI)
discord.bot.token=
statuspage.name=
banner.live=
banner.history=
discord.channel.incident=
discord.channel.dashboard=
emoji.operational=✅
emoji.degraded_performance=⚠️
emoji.partial_outage=🟠
emoji.major_outage=🔴
emoji.maintenance=🔵
check.interval.seconds=300
translations.file=translate-example.conf
translations.language=en
`;

async function runCLI() {
  console.log("=== Status Monitor - Setup (JS) ===");

  const answers = await inquirer.prompt([
    { name: "discord_bot_token", message: "Discord Bot Token:" },
    { name: "statuspage_name", message: "Statuspage name (the-subdomain before .statuspage.io):" },
    { name: "banner_live", message: "Live status banner URL (or empty):", default: "" },
    { name: "banner_history", message: "History banner URL (or empty):", default: "" },
    { name: "incident_channel", message: "Incident channel ID (numeric Discord channel id):", default: "" },
    { name: "dashboard_channel", message: "Dashboard channel ID (numeric Discord channel id):", default: "" },
    { name: "emoji_operational", message: "Emoji - operational (e.g. ✅):", default: "✅" },
    { name: "emoji_degraded_performance", message: "Emoji - degraded_performance (e.g. ⚠️):", default: "⚠️" },
    { name: "emoji_partial_outage", message: "Emoji - partial_outage (e.g. 🟠):", default: "🟠" },
    { name: "emoji_major_outage", message: "Emoji - major_outage (e.g. 🔴):", default: "🔴" },
    { name: "emoji_maintenance", message: "Emoji - maintenance (e.g. 🔵):", default: "🔵" },
    { name: "check_interval", message: "Check interval seconds (default 300):", default: "300" },
    { name: "translations_file", message: "Translations file (default translate-example.conf):", default: "translate-example.conf" },
    { name: "translations_language", message: "Translations language (e.g. en or de) (default en):", default: "en" }
  ]);

  const props = [
    `discord.bot.token=${answers.discord_bot_token.trim()}`,
    `statuspage.name=${answers.statuspage_name.trim()}`,
    `banner.live=${answers.banner_live.trim()}`,
    `banner.history=${answers.banner_history.trim()}`,
    `discord.channel.incident=${answers.incident_channel.trim()}`,
    `discord.channel.dashboard=${answers.dashboard_channel.trim()}`,
    `emoji.operational=${answers.emoji_operational.trim()}`,
    `emoji.degraded_performance=${answers.emoji_degraded_performance.trim()}`,
    `emoji.partial_outage=${answers.emoji_partial_outage.trim()}`,
    `emoji.major_outage=${answers.emoji_major_outage.trim()}`,
    `emoji.maintenance=${answers.emoji_maintenance.trim()}`,
    `check.interval.seconds=${answers.check_interval.trim() || "300"}`,
    `translations.file=${answers.translations_file.trim() || "translate-example.conf"}`,
    `translations.language=${answers.translations_language.trim() || "en"}`
  ].join("\n");

  await fs.writeFile(path.resolve("config.properties"), props, { encoding: "utf8" });
  console.log("Wrote config.properties");

  const trPath = path.resolve(answers.translations_file || "translate-example.conf");
  try {
    await fs.access(trPath);
    console.log(`${trPath} already exists — not overwriting.`);
  } catch {
    await fs.writeFile(trPath, TRANSLATIONS_EXAMPLE, { encoding: "utf8" });
    console.log(`Wrote ${trPath}`);
  }

  try {
    await fs.access("config.properties.example");
    console.log("config.properties.example already exists — not overwriting.");
  } catch {
    await fs.writeFile("config.properties.example", CONFIG_EXAMPLE, { encoding: "utf8" });
    console.log("Wrote config.properties.example");
  }

  console.log("Setup complete. Die Dateien wurden im Projekt-Root abgelegt.");
}

runCLI().catch(err => {
  console.error("Fehler im Setup:", err);
  process.exit(1);
});
