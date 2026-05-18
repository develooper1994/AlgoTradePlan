# Migration and Upgrade

Scripts:
- `scripts/migrate_data.py`
- `scripts/validate_migration.py`
- `scripts/backup_db.py`
- `scripts/restore_db.py`

Recommended flow:
1. backup
2. migration dry-run
3. validator execution
4. restore on failure
