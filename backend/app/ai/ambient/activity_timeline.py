from datetime import datetime
from typing import Any, Dict

from app.ai.ambient.context_watcher import context_watcher


class ActivityTimeline:
    def __init__(self):
        self.categories = {
            "coding": ["Code.exe", "pycharm64.exe", "WindowsTerminal.exe", "cmd.exe", "powershell.exe"],
            "browsing": ["chrome.exe", "firefox.exe", "msedge.exe", "brave.exe"],
            "communication": ["slack.exe", "Discord.exe", "Teams.exe", "OUTLOOK.EXE"],
            "documents": ["WINWORD.EXE", "EXCEL.EXE", "Notion.exe", "Obsidian.exe"],
            "media": ["Spotify.exe", "vlc.exe"],
        }

    def _categorize_app(self, app_name: str) -> str:
        for cat, apps in self.categories.items():
            if any(app.lower() == app_name.lower() for app in apps):
                return cat
        return "other"

    def get_productivity_stats(self, hours: int = 24) -> Dict[str, Any]:
        sessions = context_watcher.get_sessions(hours)

        focus_time_mins = 0.0
        context_switch_count = len(sessions) - 1 if sessions else 0
        longest_streak_mins = 0.0

        current_streak = 0.0

        app_breakdown: Dict[str, float] = {}

        for s in sessions:
            cat = self._categorize_app(s.app_name)
            if cat in ["coding", "documents", "communication"]:
                focus_time_mins += s.duration_minutes
                current_streak += s.duration_minutes
                longest_streak_mins = max(longest_streak_mins, current_streak)
            else:
                current_streak = 0.0

            app_breakdown[s.app_name] = app_breakdown.get(s.app_name, 0.0) + s.duration_minutes

        return {
            "focus_time_minutes": focus_time_mins,
            "context_switches": max(0, context_switch_count),
            "longest_focus_streak_minutes": longest_streak_mins,
            "app_breakdown": app_breakdown,
        }

    def get_daily_summary(self, target_date: datetime | None = None) -> str:
        if not target_date:
            target_date = datetime.now()

        sessions = context_watcher.get_sessions(24)

        day_sessions = [s for s in sessions if s.start_time.date() == target_date.date()]

        if not day_sessions:
            return "No activity recorded for this day."

        coding_time = sum(
            s.duration_minutes for s in day_sessions if self._categorize_app(s.app_name) == "coding"
        )
        browsing_time = sum(
            s.duration_minutes for s in day_sessions if self._categorize_app(s.app_name) == "browsing"
        )

        c_h = int(coding_time // 60)
        c_m = int(coding_time % 60)

        b_h = int(browsing_time // 60)
        b_m = int(browsing_time % 60)

        summary = "You spent "
        if c_h > 0 or c_m > 0:
            summary += f"{c_h} hours and {c_m} minutes coding, "
        if b_h > 0 or b_m > 0:
            summary += f"{b_h} hours and {b_m} minutes browsing, "

        summary = summary.rstrip(", ")
        if summary == "You spent":
            summary = "You had varied activity across other applications."

        return summary


activity_timeline = ActivityTimeline()
