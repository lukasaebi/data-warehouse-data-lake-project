#!/bin/bash

# Definiere die Freunde und deren Buckets als Assoziatives Array
declare -A FRIEND_BUCKETS=(
    [CARLOS]="aviations3 "
    [LUKAS]="BUCKET1 BUCKET2 BUCKET3"
)

# Ziel-Bucket-Mapping
declare -A TARGET_BUCKETS=(
    [CARLOS]="projectdatacombined"
    [LUKAS]="projectdatacombined"
)

# Schleife durch Freunde und ihre Buckets
for FRIEND in "${!FRIEND_BUCKETS[@]}"; do
    TARGET=${TARGET_BUCKETS[$FRIEND]}
    for BUCKET in ${FRIEND_BUCKETS[$FRIEND]}; do
        echo "Starte Synchronisierung von $FRIEND: $BUCKET nach $TARGET..."
        aws s3 sync s3://$BUCKET s3://$TARGET/$FRIEND/$BUCKET
        echo "Synchronisierung von $FRIEND: $BUCKET abgeschlossen."
    done
done