# Liste der Buckets deines Freundes
CARLOS_BUCKETS=("aviations3")

#LUKAS_BUCKETS=(".....")

# Dein Ziel-Bucket
MY_BUCKET="projectdatacombined"

# Schleife durch die Buckets deines Freundes und kopiere die Inhalte
for BUCKET in "${CARLOS_BUCKETS[@]}"; do
    echo "Kopiere Dateien von $BUCKET nach $MY_BUCKET..."
    aws s3 sync s3://$BUCKET s3://$MY_BUCKET/
    echo "Kopieren von $BUCKET abgeschlossen."
done


# Synchronisierung von Freund 2
#for BUCKET in "${LUKAS_BUCKETS[@]}"; do
    #echo "Starte Synchronisierung von Freund 2: $BUCKET nach $MY_BUCKET..."
    #aws s3 sync s3://$BUCKET s3://$MY_BUCKET
    #echo "Synchronisierung von Freund 2: $BUCKET abgeschlossen."
#done