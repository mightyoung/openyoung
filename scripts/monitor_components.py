#!/usr/bin/env python3
"""
Component Status Monitor
Monitors multiple components every 3 seconds for 60 seconds
"""

import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path

# Configuration
CHECK_INTERVAL = 3  # seconds
TOTAL_DURATION = 60  # seconds

# Paths
BASE_DIR = Path("/Users/muyi/Downloads/dev/openyoung")
DATACENTER_DIR = BASE_DIR / ".young"
SKILLS_DIR = BASE_DIR / "src" / "skills"
MCPS_FILE = BASE_DIR / "packages" / "mcp-github" / "mcp.json"

# Files to monitor
FILES_TO_WATCH = {
    "traces": DATACENTER_DIR / "traces.json",
    "evaluations": DATACENTER_DIR / "evaluations.json",
    "genes": DATACENTER_DIR / "genes.json",
    "capsules": DATACENTER_DIR / "capsules.json",
}


def get_file_hash(filepath):
    """Get MD5 hash of a file"""
    if not filepath.exists():
        return None
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def get_file_content(filepath):
    """Get content summary of a file"""
    if not filepath.exists():
        return None
    with open(filepath) as f:
        try:
            data = json.load(f)
            return data
        except json.JSONDecodeError:
            return f.read()


def get_skills_files():
    """Get list of files in skills directory"""
    if not SKILLS_DIR.exists():
        return []
    files = list(SKILLS_DIR.glob("*.py"))
    return [f.name for f in files]


def get_mcps_config():
    """Get MCP configuration"""
    if not MCPS_FILE.exists():
        return None
    with open(MCPS_FILE) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None


def get_stats_summary(data, file_type):
    """Get summary statistics for a file"""
    if data is None:
        return "N/A"

    if isinstance(data, list):
        count = len(data)
        if count == 0:
            return "empty list"

        if file_type == "traces":
            success_count = sum(1 for item in data if item.get("status") == "success")
            return f"{count} traces ({success_count} success)"

        elif file_type == "evaluations":
            avg_score = sum(item.get("score", 0) for item in data) / count
            return f"{count} evaluations (avg: {avg_score:.2f})"

        elif file_type == "genes":
            categories = set(item.get("category") for item in data)
            return f"{count} genes (categories: {', '.join(categories)})"

        elif file_type == "capsules":
            triggers = set()
            for item in data:
                triggers.update(item.get("trigger", []))
            return f"{count} capsules (triggers: {', '.join(triggers)})"

        return f"{count} items"

    return str(data)


class ComponentMonitor:
    def __init__(self):
        self.state = {}
        self.changes = []
        self.initial_state = self._capture_state()
        self.state = self.initial_state.copy()

    def _capture_state(self):
        """Capture current state of all components"""
        state = {}

        # Datacenter - traces
        traces_content = get_file_content(FILES_TO_WATCH["traces"])
        state["traces_hash"] = get_file_hash(FILES_TO_WATCH["traces"])
        state["traces_count"] = len(traces_content) if isinstance(traces_content, list) else 0
        state["traces_summary"] = get_stats_summary(traces_content, "traces")

        # Datacenter - evaluations
        evaluations_content = get_file_content(FILES_TO_WATCH["evaluations"])
        state["evaluations_hash"] = get_file_hash(FILES_TO_WATCH["evaluations"])
        state["evaluations_count"] = (
            len(evaluations_content) if isinstance(evaluations_content, list) else 0
        )
        state["evaluations_summary"] = get_stats_summary(evaluations_content, "evaluations")

        # Evolver - genes
        genes_content = get_file_content(FILES_TO_WATCH["genes"])
        state["genes_hash"] = get_file_hash(FILES_TO_WATCH["genes"])
        state["genes_count"] = len(genes_content) if isinstance(genes_content, list) else 0
        state["genes_summary"] = get_stats_summary(genes_content, "genes")

        # Evolver - capsules
        capsules_content = get_file_content(FILES_TO_WATCH["capsules"])
        state["capsules_hash"] = get_file_hash(FILES_TO_WATCH["capsules"])
        state["capsules_count"] = len(capsules_content) if isinstance(capsules_content, list) else 0
        state["capsules_summary"] = get_stats_summary(capsules_content, "capsules")

        # Skills
        state["skills_files"] = get_skills_files()
        state["skills_count"] = len(state["skills_files"])

        # MCPs
        state["mcps_config"] = get_mcps_config()

        return state

    def check_for_changes(self, check_num):
        """Check for changes since last check"""
        new_state = self._capture_state()
        changes = []

        # Check each key for changes
        for key in new_state:
            if key not in self.state:
                changes.append(f"  + New key: {key}")
            elif new_state[key] != self.state[key]:
                if key == "skills_files":
                    old_set = set(self.state[key])
                    new_set = set(new_state[key])
                    added = new_set - old_set
                    removed = old_set - new_set
                    if added:
                        changes.append(f"  + Skills added: {added}")
                    if removed:
                        changes.append(f"  - Skills removed: {removed}")
                elif key == "mcps_config":
                    changes.append("  ~ MCPs config updated")
                elif "hash" in key:
                    changes.append(f"  ~ File content changed: {key.replace('_hash', '')}")
                else:
                    changes.append(f"  ~ {key}: {self.state[key]} -> {new_state[key]}")

        self.state = new_state
        return changes

    def get_current_status(self):
        """Get formatted current status"""
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append(f"  Status Check at {datetime.now().strftime('%H:%M:%S')}")
        lines.append("=" * 60)

        # Datacenter
        lines.append("\n[1] Datacenter (.young/)")
        lines.append(f"  - traces.json:   {self.state['traces_summary']}")
        lines.append(f"  - evaluations.json: {self.state['evaluations_summary']}")

        # Evolver
        lines.append("\n[2] Evolver (genes/capsules)")
        lines.append(f"  - genes.json:    {self.state['genes_summary']}")
        lines.append(f"  - capsules.json: {self.state['capsules_summary']}")

        # Evaluation (included in datacenter)
        lines.append("\n[3] Evaluation")
        lines.append(f"  - Results: {self.state['evaluations_summary']}")

        # Skills
        lines.append("\n[4] Skills (src/skills/)")
        lines.append(
            f"  - Files: {self.state['skills_count']} ({', '.join(self.state['skills_files'])})"
        )

        # MCPs
        lines.append("\n[5] MCPs")
        if self.state["mcps_config"]:
            servers = list(self.state["mcps_config"].get("mcpServers", {}).keys())
            lines.append(f"  - Configured servers: {', '.join(servers) if servers else 'none'}")
        else:
            lines.append("  - Config: Not found")

        return "\n".join(lines)


def main():
    print("=" * 60)
    print("  Component Status Monitor")
    print("=" * 60)
    print(f"  Check interval: {CHECK_INTERVAL} seconds")
    print(f"  Total duration: {TOTAL_DURATION} seconds")
    print("=" * 60)

    monitor = ComponentMonitor()

    # Print initial state
    print(monitor.get_current_status())

    check_count = 0
    total_checks = TOTAL_DURATION // CHECK_INTERVAL

    for i in range(total_checks):
        time.sleep(CHECK_INTERVAL)
        check_count += 1

        print(f"\n--- Check #{check_count}/{total_checks} ---")
        changes = monitor.check_for_changes(check_count)

        if changes:
            print("Changes detected:")
            for change in changes:
                print(change)
        else:
            print("No changes detected.")

        # Always show current status
        print(monitor.get_current_status())

    print("\n" + "=" * 60)
    print("  Monitoring Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
