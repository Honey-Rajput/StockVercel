"""
Scheduler Module
Automatically runs the analysis pipeline at configured times.
"""
import signal
import sys
from datetime import datetime

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import config


def run_scheduled_analysis():
    """Run the full analysis pipeline (called by scheduler)."""
    from recommendation_engine import run_full_analysis, save_results
    from alerts import send_alerts

    print(f"\n⏰ Scheduled run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        results = run_full_analysis()
        save_results(results)
        send_alerts(results)
        print("✅ Scheduled run complete!\n")
    except Exception as e:
        print(f"❌ Scheduled run failed: {e}\n")


def start_scheduler():
    """Start the APScheduler with configured times."""
    tz = pytz.timezone(config.TIMEZONE)
    scheduler = BlockingScheduler(timezone=tz)

    for name, time_str in config.SCHEDULE_TIMES.items():
        hour, minute = time_str.split(":")
        trigger = CronTrigger(
            day_of_week="mon-fri",
            hour=int(hour),
            minute=int(minute),
            timezone=tz,
        )
        scheduler.add_job(
            run_scheduled_analysis,
            trigger=trigger,
            id=name,
            name=f"Stock Analysis ({name})",
            misfire_grace_time=300,
        )
        print(f"  📅 Scheduled '{name}' at {time_str} IST (Mon-Fri)")

    # Graceful shutdown
    def shutdown(signum, frame):
        print("\n🛑 Shutting down scheduler...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("\n🚀 Scheduler started! Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")


if __name__ == "__main__":
    print("=" * 50)
    print("  🤖 Stock Analysis Scheduler")
    print("=" * 50)
    start_scheduler()
