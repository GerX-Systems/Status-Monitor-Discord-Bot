package com.gerx.statusmonitor;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.DirectoryStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.util.Scanner;

public class CLI {
    private static final String TRANSLATIONS_EXAMPLE = "# Example translations file\n# Format: key=English phrase\n# Copy and create lang/<lang>.conf (e.g. lang/de.conf) replacing values with translations.\n\n" +
            "none=All systems are operational\n" +
            "minor=Minor restriction\n" +
            "major=Major outage\n" +
            "critical=Critical failure\n" +
            "maintenance=Maintenance work\n" +
            "investigating=Will be examined\n" +
            "identified=Cause identified\n" +
            "monitoring=It is being observed.\n" +
            "resolved=Fixed\n" +
            "operational=Operational\n" +
            "degraded_performance=Limited performance\n" +
            "partial_outage=Partial failure\n" +
            "major_outage=Severe failure\n" +
            "under_maintenance=Maintenance work\n";

    private static final String ENG_JSON = "{\n" +
            "  \"none\": \"All systems are operational\",\n" +
            "  \"minor\": \"Minor restriction\",\n" +
            "  \"major\": \"Major outage\",\n" +
            "  \"critical\": \"Critical failure\",\n" +
            "  \"maintenance\": \"Maintenance work\",\n" +
            "  \"investigating\": \"Will be examined\",\n" +
            "  \"identified\": \"Cause identified\",\n" +
            "  \"monitoring\": \"It is being observed.\",\n" +
            "  \"resolved\": \"Fixed\",\n" +
            "  \"operational\": \"Operational\",\n" +
            "  \"degraded_performance\": \"Limited performance\",\n" +
            "  \"partial_outage\": \"Partial failure\",\n" +
            "  \"major_outage\": \"Severe failure\",\n" +
            "  \"under_maintenance\": \"Maintenance work\"\n" +
            "}";

    public static void main(String[] args) throws IOException {
        Scanner sc = new Scanner(System.in);
        Properties p = new Properties();

        System.out.println("=== Status Monitor Discord Bot - Setup CLI ===");
        System.out.print("Discord Bot Token: ");
        p.setProperty("discord.bot.token", sc.nextLine().trim());

        System.out.print("Statuspage name (the-subdomain before .statuspage.io): ");
        p.setProperty("statuspage.name", sc.nextLine().trim());

        System.out.print("Live status banner URL (or empty): ");
        p.setProperty("banner.live", sc.nextLine().trim());

        System.out.print("History banner URL (or empty): ");
        p.setProperty("banner.history", sc.nextLine().trim());

        System.out.print("Incident channel ID (numeric Discord channel id): ");
        p.setProperty("discord.channel.incident", sc.nextLine().trim());

        System.out.print("Dashboard channel ID (numeric Discord channel id): ");
        p.setProperty("discord.channel.dashboard", sc.nextLine().trim());

        System.out.print("Emoji - operational (e.g. ✅): ");
        p.setProperty("emoji.operational", sc.nextLine().trim());

        System.out.print("Emoji - degraded_performance (e.g. ⚠️): ");
        p.setProperty("emoji.degraded_performance", sc.nextLine().trim());

        System.out.print("Emoji - partial_outage (e.g. 🟠): ");
        p.setProperty("emoji.partial_outage", sc.nextLine().trim());

        System.out.print("Emoji - major_outage (e.g. 🔴): ");
        p.setProperty("emoji.major_outage", sc.nextLine().trim());

        System.out.print("Emoji - maintenance (e.g. 🔵): ");
        p.setProperty("emoji.maintenance", sc.nextLine().trim());

        System.out.print("Check interval seconds (default 300): ");
        String interval = sc.nextLine().trim();
        if (interval.isBlank()) interval = "300";
        p.setProperty("check.interval.seconds", interval);

        // ensure lang dir and default files
        Path langDir = Path.of("lang");
        if (Files.notExists(langDir)) Files.createDirectories(langDir);
        Path engJson = langDir.resolve("eng.json");
        if (Files.notExists(engJson)) Files.writeString(engJson, ENG_JSON);
        Path conf = langDir.resolve("translate-example.conf");
        if (Files.notExists(conf)) Files.writeString(conf, TRANSLATIONS_EXAMPLE);

        // detect language files
        List<Path> langFiles = new ArrayList<>();
        try (DirectoryStream<Path> ds = Files.newDirectoryStream(langDir)) {
            for (Path pth : ds) {
                String name = pth.getFileName().toString().toLowerCase();
                if (name.endsWith(".json") || name.endsWith(".conf")) langFiles.add(pth);
            }
        }

        // build choices
        List<String> labels = new ArrayList<>();
        for (Path pth : langFiles) {
            String fname = pth.getFileName().toString();
            String base = fname.contains(".") ? fname.substring(0, fname.lastIndexOf('.')) : fname;
            if (base.equalsIgnoreCase("eng")) base = "en";
            labels.add(base + " (" + "lang/" + fname + ")");
        }
        if (labels.isEmpty()) labels.add("en (lang/eng.json)");

        System.out.println("Available languages:");
        for (int i=0;i<labels.size();i++) System.out.println((i+1) + ") " + labels.get(i));
        System.out.print("Select language by number (default 1): ");
        String sel = sc.nextLine().trim();
        int idx = 1;
        try { if (!sel.isBlank()) idx = Integer.parseInt(sel); } catch (Exception e) { idx = 1; }
        if (idx < 1) idx = 1; if (idx > labels.size()) idx = 1;

        String chosenFile = "lang/eng.json";
        String chosenLang = "en";
        if (!langFiles.isEmpty()) {
            Path chosen = langFiles.get(idx-1);
            String fname = chosen.getFileName().toString();
            chosenFile = "lang/" + fname;
            String base = fname.contains(".") ? fname.substring(0, fname.lastIndexOf('.')) : fname;
            if (base.equalsIgnoreCase("eng")) base = "en";
            chosenLang = base;
        }

        p.setProperty("translations.file", chosenFile);
        p.setProperty("translations.language", chosenLang);

        Path cfgFile = Path.of("config.properties");
        try (PrintWriter pw = new PrintWriter(Files.newBufferedWriter(cfgFile))) {
            p.store(pw, "Generated by Status Monitor CLI");
        }

        System.out.println("Wrote config.properties and translation file (if not present).");
        System.out.println("You can now run: java -jar target/StatusMonitorDiscordBot-0.1.0-jar-with-dependencies.jar");
    }
}
