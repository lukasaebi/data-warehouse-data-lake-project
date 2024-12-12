# List of your friend's buckets
CARLOS_BUCKETS=("aviations3")


# Your target bucket
MY_BUCKET="hslu-project-data"

# Loop through your friend's buckets and copy the content
for BUCKET in "${CARLOS_BUCKETS[@]}"; do
    echo "Kopiere Dateien von $BUCKET nach $MY_BUCKET..."
    aws s3 sync s3://$BUCKET s3://$MY_BUCKET/aviations3
    echo "Kopieren von $BUCKET abgeschlossen."
done

