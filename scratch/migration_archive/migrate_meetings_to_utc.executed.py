# ==============================================================================
# HISTORICAL DATABASE MIGRATION SCRIPT (EXECUTED)
# ==============================================================================
# Status: COMPLETED
# Executed At: 2026-06-10 (Successfully applied to live database)
# Purpose: Migrated Meeting.scheduled_at from naive IST to naive UTC format.
#
# WARNING: Do NOT re-run this script!
# Running this script again will double-shift dates, corrupting database values.
# Retained strictly for audit trail and historical record purposes.
# ==============================================================================

import os
import sys
from datetime import datetime, timedelta, timezone

# Adjust path to import Flask app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend')))
from app import create_app
from extensions import db
from models import Meeting

def main():
    print("[ERROR] This migration has already been executed. Aborting to prevent data corruption.")
    sys.exit(1)

if __name__ == '__main__':
    main()
