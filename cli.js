import inquirer from "inquirer";
import fs from "fs/promises";
import path from "path";

const TRANSLATIONS_EXAMPLE = `# Example translations file
# Format: key=English phrase
# Copy and create lang/<lang>.conf (e.g. lang/de.conf) replacing values with translations.

none=All systems are operational
minor=Minor restriction
major=Major outage
critical=Critical failure
maintenance=Maintenance work
investigating=Will be examined
identified=Cause identified
monitoring=It is being observed.
resolved=Fixed
operational=Operational
degraded_performance=Limited performance
partial_outage=Partial failure
major_outage=Severe failure
under_maintenance=Maintenance work
`;

const ENG_JSON = `{
  "none": "All systems are operational",
  "minor": "Minor restriction",
  "major": "Major outage",
  "critical": "Critical failure",
  "maintenance": "Maintenance work",
  "investigating": "Will be examined",
  "identified": "Cause identified",
  "monitoring": "It is being observed.",
  "resolved": "Fixed",
  "operational": "Operational",
  "degraded_performance": "Limited performance",
  "partial_outage": "Partial failure",
  "major_outage": "Severe failure",
  "under_maintenance": "Maintenance work"
}`;

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
translations.file=lang/eng.json
translations.language=en
`;

async function ensureLangFiles() {
  const langDir = path.resolve('lang');
  try { await fs.mkdir(langDir, { recursive: true }); } catch(e){}

  const engJsonPath = path.join(langDir, 'eng.json');
  try {
    await fs.access(engJsonPath);
  } catch {
    await fs.writeFile(engJsonPath, ENG_JSON, { encoding: 'utf8' });
    console.log(`Wrote ${engJsonPath}`);
  }

  const confPath = path.join(langDir, 'translate-example.conf');
  try { await fs.access(confPath); } catch {
    await fs.writeFile(confPath, TRANSLATIONS_EXAMPLE, { encoding: 'utf8' });
    console.log(`Wrote ${confPath}`);
  }
}

async function detectLanguages() {
  const langDir = path.resolve('lang');
  const list = [];
  try {
    const files = await fs.readdir(langDir);
    for (const f of files) {
      const ext = path.extname(f).toLowerCase();
      if (ext === '.json' || ext === '.conf') {
        let base = path.basename(f, ext);
        if (base.toLowerCase() === 'eng') base = 'en';
        list.push({ lang: base.toLowerCase(), file: path.join('lang', f) });
      }
    }
  } catch (e) {
    // ignore
  }
  // ensure 'en' present
  if (!list.find(l => l.lang === 'en')) list.unshift({ lang: 'en', file: 'lang/eng.json' });
  return list;
}

async function runCLI() {
  console.log("=== Status Monitor - Setup (JS) ===");

  await ensureLangFiles();
  const langs = await detectLanguages();

  const languageChoices = langs.map(l => ({ name: `${l.lang} (${l.file})`, value: l }));

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

    { type: 'list', name: 'translations_choice', message: 'Select translations language/file:', choices: languageChoices, default: 0 }
  ]);

  const selected = answers.translations_choice;
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
    `translations.file=${selected.file}`,
    `translations.language=${selected.lang}`
  ].join("\n");

  await fs.writeFile(path.resolve("config.properties"), props, { encoding: "utf8" });
  console.log("Wrote config.properties");

  console.log("Setup complete. Die Dateien wurden im Projekt-Root abgelegt.");
}

runCLI().catch(err => {
  console.error("Fehler im Setup:", err);
  process.exit(1);
});
