#!/bin/bash
# PostgreSQL Migration Script
# Dumps all PostgreSQL clusters from local workstation
# Restores to Ionos VM100 (wolf-postgres)

set -e

# Source (local workstation)
LOCAL_HOST="100.110.82.181"

# Target (Ionos VM100 - update after provisioning)
IONOS_HOST="${IONOS_POSTGRES_HOST:-ionos-vm100.ts.net}"
IONOS_USER="wolf"

# Clusters to migrate
CLUSTERS=(
    "wolf_logic:5433:wolf:wolflogic2024"
    "authentik:3306:authentik:wolflogic2024"
    "gemini:5436:gemini:gemini2024"
)

BACKUP_DIR="/tmp/postgres-migration-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "============================================================"
echo "POSTGRESQL MIGRATION - LOCAL TO IONOS"
echo "============================================================"
echo ""
echo "Source: $LOCAL_HOST (workstation)"
echo "Target: $IONOS_HOST (Ionos VM100)"
echo "Backup directory: $BACKUP_DIR"
echo ""
echo "Clusters to migrate:"
for cluster in "${CLUSTERS[@]}"; do
    IFS=':' read -r db port user pass <<< "$cluster"
    echo "  - $db @ $port"
done
echo ""
echo "============================================================"
echo ""

# Step 1: Dump all clusters locally
echo "STEP 1: Dumping PostgreSQL clusters from workstation..."
echo "============================================================"

for cluster in "${CLUSTERS[@]}"; do
    IFS=':' read -r db port user pass <<< "$cluster"

    echo ""
    echo "Dumping $db @ $port..."

    PGPASSWORD="$pass" pg_dump \
        -h "$LOCAL_HOST" \
        -p "$port" \
        -U "$user" \
        -d "$db" \
        -F c \
        -f "$BACKUP_DIR/${db}-${port}.dump"

    echo "✓ $db dumped successfully ($(du -h "$BACKUP_DIR/${db}-${port}.dump" | cut -f1))"
done

echo ""
echo "All clusters dumped."
echo ""

# Step 2: Transfer dumps to Ionos
echo "STEP 2: Transferring dumps to Ionos VM100..."
echo "============================================================"

ssh "$IONOS_USER@$IONOS_HOST" "mkdir -p /tmp/postgres-restore"

for cluster in "${CLUSTERS[@]}"; do
    IFS=':' read -r db port user pass <<< "$cluster"

    echo "Transferring ${db}-${port}.dump..."
    scp "$BACKUP_DIR/${db}-${port}.dump" "$IONOS_USER@$IONOS_HOST:/tmp/postgres-restore/"
    echo "✓ ${db} transferred"
done

echo ""
echo "All dumps transferred."
echo ""

# Step 3: Restore on Ionos
echo "STEP 3: Restoring PostgreSQL clusters on Ionos..."
echo "============================================================"

ssh "$IONOS_USER@$IONOS_HOST" << 'ENDSSH'
    set -e

    # Install PostgreSQL 16, 17, 18
    sudo apt update
    sudo apt install -y wget gnupg2

    # Add PostgreSQL repository
    echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | \
        sudo tee /etc/apt/sources.list.d/pgdg.list
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | \
        sudo apt-key add -

    sudo apt update
    sudo apt install -y postgresql-16 postgresql-17 postgresql-18 postgresql-contrib

    echo "PostgreSQL installed."

    # Create clusters
    echo ""
    echo "Creating PostgreSQL clusters..."

    # Cluster 1: wolf_logic (PG16 @ 5433)
    sudo pg_createcluster 16 wolf_logic --port 5433
    sudo systemctl start postgresql@16-wolf_logic
    sudo -u postgres psql -p 5433 -c "CREATE USER wolf WITH PASSWORD 'wolflogic2024';"
    sudo -u postgres psql -p 5433 -c "CREATE DATABASE wolf_logic OWNER wolf;"

    # Cluster 2: authentik (PG17 @ 3306)
    sudo pg_createcluster 17 authentik --port 3306
    sudo systemctl start postgresql@17-authentik
    sudo -u postgres psql -p 3306 -c "CREATE USER authentik WITH PASSWORD 'wolflogic2024';"
    sudo -u postgres psql -p 3306 -c "CREATE DATABASE authentik OWNER authentik;"

    # Cluster 3: gemini (PG17 @ 5436)
    sudo pg_createcluster 17 gemini --port 5436
    sudo systemctl start postgresql@17-gemini
    sudo -u postgres psql -p 5436 -c "CREATE USER gemini WITH PASSWORD 'gemini2024';"
    sudo -u postgres psql -p 5436 -c "CREATE DATABASE gemini OWNER gemini;"

    echo "✓ Clusters created"

    # Restore dumps
    echo ""
    echo "Restoring dumps..."

    PGPASSWORD=wolflogic2024 pg_restore \
        -h localhost -p 5433 -U wolf -d wolf_logic \
        -c --if-exists /tmp/postgres-restore/wolf_logic-5433.dump
    echo "✓ wolf_logic restored"

    PGPASSWORD=wolflogic2024 pg_restore \
        -h localhost -p 3306 -U authentik -d authentik \
        -c --if-exists /tmp/postgres-restore/authentik-3306.dump
    echo "✓ authentik restored"

    PGPASSWORD=gemini2024 pg_restore \
        -h localhost -p 5436 -U gemini -d gemini \
        -c --if-exists /tmp/postgres-restore/gemini-5436.dump
    echo "✓ gemini restored"

    # Configure listen addresses and authentication
    echo ""
    echo "Configuring PostgreSQL access..."

    # wolf_logic cluster
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" \
        /etc/postgresql/16/wolf_logic/postgresql.conf

    echo "host    all             all             0.0.0.0/0               scram-sha-256" | \
        sudo tee -a /etc/postgresql/16/wolf_logic/pg_hba.conf

    # authentik cluster
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" \
        /etc/postgresql/17/authentik/postgresql.conf

    echo "host    all             all             0.0.0.0/0               scram-sha-256" | \
        sudo tee -a /etc/postgresql/17/authentik/pg_hba.conf

    # gemini cluster
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" \
        /etc/postgresql/17/gemini/postgresql.conf

    echo "host    all             all             0.0.0.0/0               scram-sha-256" | \
        sudo tee -a /etc/postgresql/17/gemini/pg_hba.conf

    # Restart clusters
    sudo systemctl restart postgresql@16-wolf_logic
    sudo systemctl restart postgresql@17-authentik
    sudo systemctl restart postgresql@17-gemini

    echo "✓ PostgreSQL configured and restarted"

    # Cleanup
    rm -rf /tmp/postgres-restore

ENDSSH

echo ""
echo "============================================================"
echo "MIGRATION COMPLETE"
echo "============================================================"
echo ""
echo "Verify migration:"
echo "  ssh $IONOS_USER@$IONOS_HOST"
echo "  PGPASSWORD=wolflogic2024 psql -h localhost -p 5433 -U wolf -d wolf_logic -c 'SELECT COUNT(*) FROM memories;'"
echo ""
echo "Update connection strings in applications to point to:"
echo "  wolf_logic: $IONOS_HOST:5433"
echo "  authentik: $IONOS_HOST:3306"
echo "  gemini: $IONOS_HOST:5436"
echo ""
