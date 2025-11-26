# Database Migrations Guide

This project uses **Flask-Migrate** (Alembic) for database schema management.

## Quick Reference

```bash
# Initialize migrations (only run once - already done)
flask db init

# Create a new migration after changing models
flask db migrate -m "Description of changes"

# Apply migrations to database
flask db upgrade

# Rollback last migration
flask db downgrade

# Show migration history
flask db history

# Show current migration version
flask db current
```

## Common Workflows

### 1. Fresh Database Setup

```bash
# Create the database
createdb vibe-stock-market-predictor-development

# Apply all migrations
mise exec -- flask db upgrade

# Seed with sample data (optional)
mise exec -- python seed_data.py
```

### 2. Making Model Changes

When you modify models in `models.py`:

```bash
# 1. Make your changes to models.py
# 2. Generate migration
mise exec -- flask db migrate -m "Add new column to traders"

# 3. Review the generated migration file in migrations/versions/
# 4. Apply the migration
mise exec -- flask db upgrade
```

### 3. Rolling Back Changes

```bash
# Rollback the last migration
mise exec -- flask db downgrade

# Rollback to a specific migration
mise exec -- flask db downgrade <revision_id>
```

## Migration Files

Migrations are stored in `migrations/versions/` directory. Each migration has:
- **Upgrade function**: SQL to apply changes
- **Downgrade function**: SQL to rollback changes

## Environment Variables

Make sure `DATABASE_URL` is set in your `.env` file:

```bash
# Local development
DATABASE_URL=postgresql://localhost/vibe-stock-market-predictor-development

# Production (Heroku automatically sets this)
DATABASE_URL=postgresql://user:password@host:port/database
```

## Best Practices

1. **Always review generated migrations** - Auto-generated migrations aren't always perfect
2. **Test migrations locally first** - Never run untested migrations in production
3. **Never edit applied migrations** - Create a new migration instead
4. **Keep migrations small** - One logical change per migration
5. **Use descriptive names** - `flask db migrate -m "Clear description"`

## Deprecated Scripts

These scripts are no longer needed with Flask-Migrate:
- ❌ `setup_db.py` - Use `flask db upgrade` instead
- ❌ `migrate_db.py` - Use `flask db migrate` instead
- ❌ `migrate_watchlist_system.py` - Integrated into model migrations

## Troubleshooting

### "Table already exists" error
This means tables were created manually. Options:
1. Drop the database and start fresh (development only!)
2. Stamp the current state: `flask db stamp head`

### Migration not detected
1. Make sure you saved `models.py`
2. Restart Flask if using auto-reload
3. Check Flask-Migrate is imported in `app.py`

### Rollback fails
Some operations can't be rolled back (like dropping columns with data).
Best practice: Backup database before major migrations.

## Production Deployment (Heroku)

Heroku automatically runs migrations on deploy if you add to `release` phase in `Procfile`:

```
release: flask db upgrade
web: gunicorn app:app
```

Or run manually:
```bash
heroku run flask db upgrade --app your-app-name
```
