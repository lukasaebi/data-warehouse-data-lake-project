#!/bin/bash

# Liste der Buckets
BUCKETS=("aviations3")

# JSON-Datei mit der Richtlinie
POLICY_FILE="bucket-policy.json"

# Schleife durch die Buckets und wende die Richtlinie an
for BUCKET in "${BUCKETS[@]}"; do
    echo "Setze Richtlinie für $BUCKET"
    aws s3api put-bucket-policy --bucket $BUCKET --policy file://$POLICY_FILE
    echo "Richtlinie erfolgreich angewendet für $BUCKET"
done
