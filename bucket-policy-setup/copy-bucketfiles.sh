#!/bin/bash

# Liste der Buckets deines Freundes
FRIEND_BUCKETS=("freunds-bucket-1" "freunds-bucket-2" "freunds-bucket-3")

# Dein Ziel-Bucket
MY_BUCKET="mein-s3-bucket"

# Schleife durch die Buckets deines Freundes und kopiere die Inhalte
for BUCKET in "${FRIEND_BUCKETS[@]}"; do
    echo "Kopiere Dateien von $BUCKET nach $MY_BUCKET..."
    aws s3 sync s3://$BUCKET s3://$MY_BUCKET/
    echo "Kopieren von $BUCKET abgeschlossen."
done
