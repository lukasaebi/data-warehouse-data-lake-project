# S3 BUCKET OPERATIONS

**Prerquisite**:
* You need to have your CLI configured. If you haven't, follow the instructions under point 4 under `lambda_functions/README.md`.

### 1. Create an S3 Bucket
```bash
bash s3_buckets/create_bucket.sh <buckt-name>
```
**See**:
* [This page](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html) for bucket naming rules. The most important one: <u>don't use underscores</u>.

### 2. Delete an S3 Bucket
```bash
bash s3_buckets/delete_bucket.sh <buckt-name>
```