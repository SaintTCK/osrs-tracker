import json
import os
import urllib.request
from datetime import datetime, timezone

USERNAME = "sainttck"
API_URL = f"https://api.wiseoldman.net/v2/players/{USERNAME}"

DATA_DIR = "data"
LATEST_FILE = os.path.join(DATA_DIR, "latest.json")
PREVIOUS_FILE = os.path.join(DATA_DIR, "previous.json")
CHANGES_FILE = os.path.join(DATA_DIR, "changes.txt")
LATEST_TEXT_FILE = os.path.join(DATA_DIR, "latest.txt")

def fetch_wom_profile():
    request = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "SaintTCK OSRS Tracker - GitHub Actions"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_snapshot(profile):
    snapshot = profile.get("latestSnapshot", {})
    data = snapshot.get("data", {})

    skills = data.get("skills", {})
    bosses = data.get("bosses", {})
    activities = data.get("activities", {})

    simplified_skills = {}
    for skill_name, skill_data in skills.items():
        simplified_skills[skill_name] = {
            "rank": skill_data.get("rank"),
            "level": skill_data.get("level"),
            "experience": skill_data.get("experience"),
        }

    simplified_bosses = {}
    for boss_name, boss_data in bosses.items():
        simplified_bosses[boss_name] = {
            "rank": boss_data.get("rank"),
            "kills": boss_data.get("kills"),
        }

    simplified_activities = {}
    for activity_name, activity_data in activities.items():
        simplified_activities[activity_name] = {
            "rank": activity_data.get("rank"),
            "score": activity_data.get("score"),
        }

    return {
        "username": profile.get("username"),
        "displayName": profile.get("displayName"),
        "type": profile.get("type"),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "skills": simplified_skills,
        "bosses": simplified_bosses,
        "activities": simplified_activities,
    }


def load_json(path):
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)


def compare_snapshots(old, new):
    changes = []

    if not old:
        changes.append("Initial snapshot created.")
        return changes

    old_skills = old.get("skills", {})
    new_skills = new.get("skills", {})

    for skill, new_data in new_skills.items():
        old_data = old_skills.get(skill, {})

        old_level = old_data.get("level")
        new_level = new_data.get("level")

        if old_level is not None and new_level is not None and new_level > old_level:
            changes.append(f"{skill}: level {old_level} → {new_level}")

    old_bosses = old.get("bosses", {})
    new_bosses = new.get("bosses", {})

    for boss, new_data in new_bosses.items():
        old_data = old_bosses.get(boss, {})

        old_kills = old_data.get("kills")
        new_kills = new_data.get("kills")

        if old_kills is not None and new_kills is not None and new_kills > old_kills:
            gained = new_kills - old_kills
            changes.append(f"{boss}: +{gained} KC ({old_kills} → {new_kills})")

    return changes

def save_latest_text(path, data):
    skills = data.get("skills", {})
    bosses = data.get("bosses", {})
    activities = data.get("activities", {})

    lines = [
        "SaintTCK OSRS Tracker",
        "======================",
        "",
        f"Username: {data.get('username')}",
        f"Display Name: {data.get('displayName')}",
        f"Account Type: {data.get('type')}",
        f"Updated At: {data.get('updatedAt')}",
        "",
        "Skills",
        "------",
    ]

    for skill, info in sorted(skills.items()):
        lines.append(
            f"{skill}: level {info.get('level')}, "
            f"xp {info.get('experience')}, "
            f"rank {info.get('rank')}"
        )

    lines.extend(["", "Bosses", "------"])

    for boss, info in sorted(bosses.items()):
        kills = info.get("kills")
        if kills and kills > 0:
            lines.append(
                f"{boss}: {kills} KC, rank {info.get('rank')}"
            )

    lines.extend(["", "Activities", "----------"])

    for activity, info in sorted(activities.items()):
        score = info.get("score")
        if score and score > 0:
            lines.append(
                f"{activity}: {score}, rank {info.get('rank')}"
            )

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))
        file.write("\n")

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    previous = load_json(LATEST_FILE)

    profile = fetch_wom_profile()
    latest = extract_snapshot(profile)

    if previous:
        save_json(PREVIOUS_FILE, previous)

    save_json(LATEST_FILE, latest)
    save_latest_text(LATEST_TEXT_FILE, latest)

changes = compare_snapshots(previous, latest)

    changes = compare_snapshots(previous, latest)

    with open(CHANGES_FILE, "w", encoding="utf-8") as file:
        file.write(f"SaintTCK OSRS tracker update\n")
        file.write(f"Checked at: {latest['updatedAt']}\n\n")

        if changes:
            file.write("Changes detected:\n")
            for change in changes:
                file.write(f"- {change}\n")
        else:
            file.write("No meaningful changes detected.\n")


if __name__ == "__main__":
    main()
