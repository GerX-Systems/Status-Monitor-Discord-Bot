import discord
from discord.ext import commands, tasks
from discord.http import Route
import aiohttp
import json
import os
import time
import traceback
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
# ENTER BOT TOKEN HERE
DISCORD_BOT_TOKEN = 'YOUR_DISCORD_BOT_TOKEN_HERE' 

# Enter the status page name (the one before the domain: [The status page name].statuspage.io)
STATUSPAGE_NAME = 'DEIN_STATUSPAGE_NAME_HIER'

# Banner URLs
LIVE_STATUS_BANNER = YOUR_LIVE_STATUS_BANNER_URL
HISTORY_VORFAELLE_BANNER = YOUR_HISTORY_BANNER_URL

INCIDENT_CHANNEL_ID = YOUR_INCIDENT_CHANNEL_ID_HERE
DASHBOARD_CHANNEL_ID = YOUR_LIVE_STATUS_DISPLAY_ID_HERE

# Emojis (IMPORTANT!!!)
operational_emoji = OPERATIONAL_EMOJI_HERE
degraded_performance_emoji = degraded_performance_emoji_here
partial_outage_emoji = partial_outage_emoji_here
major_outage_emoji = major_outage_emoji_here
under_maintenance_emoji = under_maintenance_emoji_here


# =========================================
# From here on, everything stays the same^^

STATUSPAGE_URL = f'https://{STATUSPAGE_NAME}.statuspage.io/api/v2/summary.json'
CHECK_INTERVAL_SECONDS = 300 # 5 Minuten
STATE_FILE = './status_state.json'

# ==========================================
# ÜBERSETZUNGEN & EMOJIS
# ==========================================
TRANSLATIONS = {
    "none": "Alle Systeme betriebsbereit",
    "minor": "Geringe Einschränkung",
    "major": "Großer Ausfall",
    "critical": "Kritischer Ausfall",
    "maintenance": "Wartungsarbeiten",
    "investigating": "Wird untersucht",
    "identified": "Ursache identifiziert",
    "monitoring": "Wird beobachtet",
    "resolved": "Behoben",
    "operational": "Betriebsbereit",
    "degraded_performance": "Eingeschränkte Leistung",
    "partial_outage": "Teilweiser Ausfall",
    "major_outage": "Schwerer Ausfall",
    "under_maintenance": "Wartungsarbeiten"
}

def translate(word):
    if not word: return "Unbekannt"
    return TRANSLATIONS.get(word.lower(), word.capitalize())

def get_color_for_indicator(indicator):
    colors = {
        'none': 0x2ecc71,      # Grün
        'resolved': 0x2ecc71,  # Grün
        'minor': 0xf1c40f,     # Gelb
        'major': 0xe67e22,     # Orange
        'critical': 0xe74c3c,  # Rot
        'maintenance': 0x3498db # Blau
    }
    return colors.get(indicator.lower(), 0x95a5a6)
def get_emoji_for_component(status):
    emojis = {
        "operational": f"{operational_emoji}",
        "degraded_performance": f"{degraded_performance_emoji}",
        "partial_outage": f"{partial_outage_emoji}",
        "major_outage": f"{major_outage_emoji}",
        "under_maintenance": f"{under_maintenance_emoji}"
    }
    return emojis.get(status.lower(), "❔")

def parse_iso_time(iso_str):
    if not iso_str: return 0
    try:
        clean_str = iso_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(clean_str)
        return int(dt.timestamp())
    except Exception:
        return 0

# ==========================================
# STATE MANAGEMENT
# ==========================================
last_state = {
    "indicator": "none",
    "description": "All Systems Operational",
    "known_incidents": {},
    "overview_message_id": None
}

def load_state():
    global last_state
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                last_state.update(loaded)
    except Exception as e:
        print(f"Fehler beim Laden des Status: {e}")

def save_state():
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(last_state, f, indent=4)
    except Exception as e:
        print(f"Fehler beim Speichern des Status: {e}")

# ==========================================
# DISCORD BOT SETUP
# ==========================================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Eingeloggt als {bot.user} (ID: {bot.user.id})")
    load_state()
    
    # 1. Alte Dashboard-Nachricht löschen, um Hänger zu vermeiden
    msg_id = last_state.get("overview_message_id")
    if msg_id:
        print("Lösche alte Dashboard-Nachricht für einen sauberen Neustart...")
        try:
            route = Route('DELETE', f'/channels/{DASHBOARD_CHANNEL_ID}/messages/{msg_id}')
            await bot.http.request(route)
            print("Alte Nachricht erfolgreich gelöscht.")
        except discord.NotFound:
            print("Alte Nachricht war bereits gelöscht.")
        except Exception as e:
            print(f"Konnte alte Nachricht nicht löschen (Fehler ignoriert): {e}")
        
        # ID zurücksetzen, damit er gleich eine Neue postet
        last_state["overview_message_id"] = None
        save_state()

    # 2. Schleife starten
    if not check_status.is_running():
        print("Starte 5-Minuten Überprüfungsschleife...")
        check_status.start()

@bot.event
async def on_interaction(interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data.get("custom_id", "")
    
    if custom_id == "show_history" or custom_id.startswith("history_page_"):
        page = 0
        if custom_id.startswith("history_page_"):
            try:
                page = int(custom_id.split("_")[-1])
            except:
                pass
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://{STATUSPAGE_NAME}.statuspage.io/api/v2/incidents.json') as response:
                    if response.status == 200:
                        data = await response.json()
                        all_incidents = data.get('incidents', [])
                    else:
                        all_incidents = []
        except Exception:
            all_incidents = []

        past_incidents = [i for i in all_incidents if i.get('status') in ['resolved', 'postmortem']]
        current_dt = datetime.now()
        
        # Generiere IMMER genau 12 Monate rückwärts ab dem aktuellen Monat
        months_list = []
        curr = current_dt
        for _ in range(12):
            months_list.append((curr.year, curr.month))
            month = curr.month - 1
            year = curr.year
            if month == 0:
                month, year = 12, year - 1
            curr = datetime(year, month, 1)

        per_page = 3
        total_months = len(months_list) # Sind jetzt fix 12 Monate
        start_idx = page * per_page
        end_idx = start_idx + per_page
        page_months = months_list[start_idx:end_idx]
        
        dynamic_history_components = []
        months_names = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
        
        for idx, (year, month) in enumerate(page_months):
            month_name = f"{months_names[month]} {year}"
            content_lines = [f"### {month_name}"]
            
            inc_in_month = []
            for inc in past_incidents:
                ts = parse_iso_time(inc.get('resolved_at') or inc.get('created_at'))
                if ts:
                    dt = datetime.fromtimestamp(ts)
                    if dt.year == year and dt.month == month:
                        inc_in_month.append(inc)
            
            if not inc_in_month:
                content_lines.append("Keine Vorfälle\n")
            else:
                for inc in inc_in_month:
                    title = inc.get('name', 'Unbekannter Vorfall')
                    link = inc.get('shortlink', '')
                    desc = inc.get('incident_updates', [{}])[0].get('body', 'Keine Details verfügbar.')
                    if len(desc) > 120: desc = desc[:117] + "..."
                    ts = parse_iso_time(inc.get('resolved_at') or inc.get('created_at'))
                    inc_dt = datetime.fromtimestamp(ts)
                    full_date = f"{inc_dt.day}. {months_names[inc_dt.month]} {inc_dt.year}"
                    content_lines.append(f"**[{title}]({link})**\n{desc}\n-# {full_date}\n")
            
            dynamic_history_components.append({
                "type": 10,
                "content": "\n".join(content_lines)
            })
            
            if idx < len(page_months) - 1:
                dynamic_history_components.append({
                    "type": 14,
                    "divider": True,
                    "spacing": 2
                })

        has_prev = page > 0
        has_next = end_idx < total_months

        v2_components = [
            {
                "type": 12,
                "items": [{"media": {"url": f"{HISTORY_VORFAELLE_BANNER}"}, "description": None, "spoiler": False}]
            },
            {"type": 14, "divider": True, "spacing": 2},
            {"type": 10, "content": "# Vergangene Vorfälle"},
            {"type": 14, "divider": True, "spacing": 2}
        ]

        v2_components.extend(dynamic_history_components)

        v2_components.extend([
            {"type": 14, "divider": False, "spacing": 1},
            {"type": 14, "divider": True, "spacing": 1},
            {
                "type": 1,
                "components": [
                    {
                        "type": 2, "style": 1, "label": "",
                        "emoji": {"name": "arrow_left", "id": "1533201019419230258"},
                        "disabled": not has_prev, "custom_id": f"history_page_{page - 1}"
                    },
                    {
                        "type": 2, "style": 1, "label": "",
                        "emoji": {"name": "arrow_right", "id": "1533201017326534666"},
                        "disabled": not has_next, "custom_id": f"history_page_{page + 1}"
                    }
                ]
            }
        ])

        response_type = 4 if custom_id == "show_history" else 7
        payload = {
            "type": response_type,
            "data": {
                "flags": 32832, 
                "components": [{"type": 17, "accent_color": None, "spoiler": False, "components": v2_components}]
            }
        }

        route = Route('POST', f'/interactions/{interaction.id}/{interaction.token}/callback')
        try:
            await bot.http.request(route, json=payload)
        except Exception as e:
            print(f"Fehler beim Senden des History-Embeds: {e}")

@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def check_status():
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Rufe Statuspage-Daten ab...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(STATUSPAGE_URL) as response:
                    if response.status != 200:
                        print(f"API Fehler: Status {response.status}")
                        return
                    data = await response.json()
        except Exception as e:
            print(f"Fehler bei der Verbindung zur Statuspage: {e}")
            return

        current_status = data.get('status', {})
        incidents = data.get('incidents', [])
        page_info = data.get('page', {})
        components = data.get('components', [])
        scheduled_maintenances = data.get('scheduled_maintenances', [])
        
        status_changed = False
        incident_channel = bot.get_channel(INCIDENT_CHANNEL_ID)

        # 1. Gesamt-Status & Vorfall-Updates prüfen (Für den Incident Channel)
        if current_status.get('indicator') != last_state['indicator']:
            if incident_channel:
                try:
                    embed = discord.Embed(
                        title="Systemstatus Update",
                        description=f"Der Gesamtstatus für **{page_info.get('name')}** hat sich geändert.",
                        color=get_color_for_indicator(current_status.get('indicator', 'none')),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="Neuer Status", value=translate(current_status.get('indicator', 'none')), inline=False)
                    await incident_channel.send(embed=embed)
                except Exception: pass
            
            last_state['indicator'] = current_status.get('indicator')
            last_state['description'] = current_status.get('description')
            status_changed = True

        current_incident_ids = []
        for incident in incidents:
            incident_id = incident['id']
            current_incident_ids.append(incident_id)
            latest_update = incident.get('incident_updates', [{}])[0]
            update_id = latest_update.get('id')
            known_incident = last_state['known_incidents'].get(incident_id)
            
            if not known_incident or known_incident.get('last_update_id') != update_id:
                if incident_channel:
                    try:
                        impact = incident.get('impact', 'none')
                        color_key = 'resolved' if incident.get('status') == 'resolved' else impact
                        embed = discord.Embed(
                            title=f"🚨 Vorfall Update: {incident['name']}",
                            url=incident.get('shortlink'),
                            color=get_color_for_indicator(color_key),
                            timestamp=datetime.utcnow()
                        )
                        embed.add_field(name="Status", value=translate(incident.get('status', 'unknown')), inline=True)
                        embed.add_field(name="Auswirkung", value=translate(impact), inline=True)
                        if latest_update.get('body'):
                            embed.add_field(name="Letztes Update", value=latest_update.get('body'), inline=False)
                        await incident_channel.send(embed=embed)
                    except Exception: pass
                
                last_state['known_incidents'][incident_id] = {'status': incident.get('status'), 'last_update_id': update_id}
                status_changed = True

        to_remove = [i_id for i_id in last_state['known_incidents'] if i_id not in current_incident_ids]
        for i_id in to_remove:
            del last_state['known_incidents'][i_id]
            status_changed = True

        # 2. Live Übersicht für das Dashboard aufbauen
        groups = [c for c in components if c.get('group') == True]
        ungrouped = [c for c in components if not c.get('group_id') and c.get('group') == False]
        
        description_lines = []
        for group in groups:
            description_lines.append(f"\n**{group['name']}**")
            group_comps = [c for c in components if c.get('group_id') == group['id']]
            for comp in group_comps:
                c_emoji = get_emoji_for_component(comp.get('status', 'unknown'))
                description_lines.append(f"> {c_emoji} {comp['name']}: *{translate(comp.get('status', 'unknown'))}*")
                
        if ungrouped:
            if groups: description_lines.append("\n**Weitere Dienste:**")
            for comp in ungrouped:
                c_emoji = get_emoji_for_component(comp.get('status', 'unknown'))
                description_lines.append(f"> {c_emoji} {comp['name']}: *{translate(comp.get('status', 'unknown'))}*")
                
        dynamic_text = "\n".join(description_lines)

        active_incidents_text = ""
        active_inc_list = [i for i in incidents if i.get('status') not in ['resolved', 'postmortem']]
        if active_inc_list:
            inc_lines = []
            for inc in active_inc_list:
                i_name = inc.get('name', 'Unbekannter Vorfall')
                i_status = translate(inc.get('status', 'investigating'))
                i_desc = inc.get('incident_updates', [{}])[0].get('body', 'Keine Details verfügbar.')
                inc_lines.append(f"🚨 **{i_name}**\n> **Status:** {i_status}\n> {i_desc}\n")
            active_incidents_text = "\n\n" + "\n".join(inc_lines)

        # WICHTIG: Timestamp für die ZUKUNFT berechnen (für den Countdown: "in 5 Minuten")
        next_update_ts = int(time.time() + CHECK_INTERVAL_SECONDS)

        v2_items = [
            {"type": 12, "items": [{"media": {"url": f"{LIVE_STATUS_BANNER}"}, "description": None, "spoiler": False}]},
            {"type": 14, "divider": True, "spacing": 2},
            {"type": 10, "content": "Hier findest du Eine Live Übersicht über unsere Systeme"},
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 14, "divider": False, "spacing": 2}
        ]

        active_maintenance = next((m for m in scheduled_maintenances if m.get('status') in ['scheduled', 'in_progress', 'verifying']), None)
        if active_maintenance:
            start_ts = parse_iso_time(active_maintenance.get('scheduled_for'))
            end_ts = parse_iso_time(active_maintenance.get('scheduled_until'))
            desc = active_maintenance.get('incident_updates', [{}])[0].get('body', 'Keine Beschreibung verfügbar.')
            affected_comps = ", ".join([c['name'] for c in active_maintenance.get('components', [])]) or "Keine spezifischen"

            maint_content = f"### {under_maintenance_emoji} Geplante Wartungsarbeiten\n**Beginn:** <t:{start_ts}:f>\n**Ende:** <t:{end_ts}:f>\n**Beschreibung:** {desc}\n**Betroffene Systeme:** {affected_comps}"
            v2_items.extend([
                {"type": 10, "content": maint_content},
                {"type": 14, "divider": True, "spacing": 1},
                {"type": 14, "divider": False, "spacing": 2}
            ])

        v2_items.extend([
            {"type": 10, "content": f"**Gesamt Status:** {translate(current_status.get('indicator', 'none'))}{active_incidents_text}\n{dynamic_text}"},
            {"type": 14, "divider": False, "spacing": 2},
            {"type": 14, "divider": True, "spacing": 2},
            {
                "type": 1,
                "components": [
                    {
                        "type": 2, "style": 5, "label": "Status Seite",
                        "emoji": {"name": "info", "id": "1533144603283165184"},
                        "disabled": False, "url": f"https://{STATUSPAGE_NAME}.statuspage.io/"
                    },
                    {
                        "type": 2, "style": 2, "label": "Vergangene Vorfälle",
                        "custom_id": "show_history",
                        "emoji": {"name": "history", "id": "1533150527418793984"},
                        "disabled": False
                    }
                ]
            },
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 10, "content": f"Aktualisiert <t:{next_update_ts}:R>"}
        ])

        v2_payload = {
            "flags": 32768, 
            "components": [{"type": 17, "accent_color": None, "spoiler": False, "components": v2_items}]
        }

        try:
            msg_id = last_state.get("overview_message_id")
            if msg_id:
                route = Route('PATCH', f'/channels/{DASHBOARD_CHANNEL_ID}/messages/{msg_id}')
                await bot.http.request(route, json=v2_payload)
                print(f"Dashboard erfolgreich aktualisiert. Nächstes Update in {CHECK_INTERVAL_SECONDS} Sekunden.")
            else:
                route = Route('POST', f'/channels/{DASHBOARD_CHANNEL_ID}/messages')
                response = await bot.http.request(route, json=v2_payload)
                last_state["overview_message_id"] = response["id"]
                save_state()
                print("Neues Dashboard erfolgreich gesendet.")
        except discord.NotFound:
            print("Nachricht nicht gefunden. Erstelle neue...")
            route = Route('POST', f'/channels/{DASHBOARD_CHANNEL_ID}/messages')
            response = await bot.http.request(route, json=v2_payload)
            last_state["overview_message_id"] = response["id"]
            save_state()
        except discord.HTTPException as e:
            print(f"Discord API Fehler beim Dashboard-Update: {e}")

        if status_changed:
            save_state()
            
    except Exception as e:
        print(f"🚨 Schwerwiegender Fehler im Loop (wird ignoriert, Bot läuft weiter): {e}")
        traceback.print_exc()

if __name__ == "__main__":
    if DISCORD_BOT_TOKEN == 'DEIN_BOT_TOKEN_HIER':
        print("FEHLER: Bitte trage zuerst deinen DISCORD_BOT_TOKEN in Zeile 16 im Code ein!")
    else:
        bot.run(DISCORD_BOT_TOKEN)
