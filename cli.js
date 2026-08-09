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

async function loadExistingConfig() {
  const cfgPath = path.resolve('config.properties');
  const existing = {};
  try {
    await fs.access(cfgPath);
    const content = await fs.readFile(cfgPath, { encoding: 'utf8' });
    const lines = content.split(/\r?\n/);
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eq = trimmed.indexOf('=');
      if (eq === -1) continue;
      const key = trimmed.substring(0, eq).trim();
      const val = trimmed.substring(eq + 1).trim();
      existing[key] = val;
    }
    console.log('Loaded existing config.properties (will use values as defaults).');
  } catch (e) {
    // file doesn't exist — ignore
  }
  return existing;
}

async function runCLI() {
  console.log("=== Status Monitor - Setup (JS) ===");

  await ensureLangFiles();
  const langs = await detectLanguages();

  const languageChoices = langs.map(l => ({ name: `${l.lang} (${l.file})`, value: l }));

  const existing = await loadExistingConfig();

  // find default translation index
  let defaultTranslationIndex = 0;
  if (existing['translations.file']) {
    const idx = languageChoices.findIndex(c => c.value.file === existing['translations.file']);
    if (idx !== -1) defaultTranslationIndex = idx;
  }

  const answers = await inquirer.prompt([
    { name: "discord_bot_token", message: "Discord Bot Token:", default: existing['discord.bot.token'] || '' },
    { name: "statuspage_name", message: "Statuspage name (the-subdomain before .statuspage.io):", default: existing['statuspage.name'] || '' },
    { name: "banner_live", message: "Live status banner URL (or empty):", default: existing['banner.live'] || '' },
    { name: "banner_history", message: "History banner URL (or empty):", default: existing['banner.history'] || '' },
    { name: "incident_channel", message: "Incident channel ID (numeric Discord channel id):", default: existing['discord.channel.incident'] || '' },
    { name: "dashboard_channel", message: "Dashboard channel ID (numeric Discord channel id):", default: existing['discord.channel.dashboard'] || '' },
    { name: "emoji_operational", message: "Emoji - operational (e.g. ✅):", default: existing['emoji.operational'] || '✅' },
    { name: "emoji_degraded_performance", message: "Emoji - degraded_performance (e.g. ⚠️):", default: existing['emoji.degraded_performance'] || '⚠️' },
    { name: "emoji_partial_outage", message: "Emoji - partial_outage (e.g. 🟠):", default: existing['emoji.partial_outage'] || '🟠' },
    { name: "emoji_major_outage", message: "Emoji - major_outage (e.g. 🔴):", default: existing['emoji.major_outage'] || '🔴' },
    { name: "emoji_maintenance", message: "Emoji - maintenance (e.g. 🔵):", default: existing['emoji.maintenance'] || '🔵' },
    { name: "check_interval", message: "Check interval seconds (default 300):", default: existing['check.interval.seconds'] || '300' },

    { type: 'list', name: 'translations_choice', message: 'Select translations language/file:', choices: languageChoices, default: defaultTranslationIndex }
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

  console.log("Setup complete. The files were written to the project root.");
}

runCLI().catch(err => {
  console.error("Error in setup:", err);
  process.exit(1);
});
