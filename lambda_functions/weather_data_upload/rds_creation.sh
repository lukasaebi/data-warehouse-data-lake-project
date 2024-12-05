#!/bin/bash

set -e

# Funktion für das Protokollieren von Nachrichten
log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1"
}

# Validieren von Umgebungsvariablen
validate_env_vars() {
    REQUIRED_VARS=("AWS_REGION" "DB_INSTANCE_IDENTIFIER" "DB_INSTANCE_CLASS" "ENGINE" 
                   "ALLOCATED_STORAGE" "RDS_USER" "RDS_PASSWORD" "SECURITY_GROUP_ID")
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            echo "Fehler: Die Umgebungsvariable $var ist nicht gesetzt. Bitte überprüfe die .env-Datei."
            exit 1
        fi
    done
}

# RDS-Instanz erstellen
create_rds_instance() {
    log "Erstelle RDS-Instanz '$DB_INSTANCE_IDENTIFIER'..."
    aws rds create-db-instance \
        --db-instance-identifier "$DB_INSTANCE_IDENTIFIER" \
        --db-instance-class "$DB_INSTANCE_CLASS" \
        --engine "$ENGINE" \
        --engine-version "$ENGINE_VERSION" \
        --allocated-storage "$ALLOCATED_STORAGE" \
        --master-username "$RDS_USER" \
        --master-user-password "$RDS_PASSWORD" \
        --backup-retention-period "${BACKUP_RETENTION_PERIOD:-7}" \
        --no-multi-az \
        --vpc-security-group-ids "$SECURITY_GROUP_ID" \
        --availability-zone "$(aws ec2 describe-availability-zones --region $AWS_REGION --query 'AvailabilityZones[0].ZoneName' --output text)" \
        --publicly-accessible \
        --storage-type gp2
}

# Warten, bis die Instanz verfügbar ist
wait_for_rds() {
    log "Warte auf die Verfügbarkeit der RDS-Instanz..."
    aws rds wait db-instance-available --db-instance-identifier "$DB_INSTANCE_IDENTIFIER"
}

# RDS-Endpunkt abrufen
fetch_rds_endpoint() {
    log "Abrufen des RDS-Endpunkts..."
    DB_ENDPOINT=$(aws rds describe-db-instances \
        --db-instance-identifier "$DB_INSTANCE_IDENTIFIER" \
        --query "DBInstances[0].Endpoint.Address" \
        --output text)
    log "Die RDS-Instanz '$DB_INSTANCE_IDENTIFIER' ist unter dem Endpunkt erreichbar: $DB_ENDPOINT"
}

# Umgebungsvariablen laden
log "Lade Umgebungsvariablen aus .env-Datei..."
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Fehler: .env-Datei nicht gefunden! Bitte sicherstellen, dass die Datei vorhanden ist."
    exit 1
fi

# Validieren der Umgebungsvariablen
validate_env_vars

# RDS-Instanz erstellen und Endpunkt abrufen
create_rds_instance
wait_for_rds
fetch_rds_endpoint

log "RDS-Setup erfolgreich abgeschlossen."
