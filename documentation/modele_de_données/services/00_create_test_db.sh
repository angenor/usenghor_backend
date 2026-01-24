#!/bin/bash
# Script pour créer la base de données de test
# Exécuté automatiquement au démarrage du conteneur PostgreSQL

set -e

# Créer la base de données de test si elle n'existe pas
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE usenghor_test'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'usenghor_test')\gexec

    GRANT ALL PRIVILEGES ON DATABASE usenghor_test TO $POSTGRES_USER;
EOSQL

echo "Base de données de test 'usenghor_test' créée avec succès."
