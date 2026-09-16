#!/bin/bash
# Initialize the database for the Lenny Growth Assistant

set -e

echo "Initializing database..."

# Run the initialization script
python -m app.db.init_db

echo "Database initialization complete!"
echo ""
echo "To create migrations, run:"
echo "  alembic revision --autogenerate -m 'Initial migration'"
echo ""
echo "To apply migrations, run:"
echo "  alembic upgrade head"
