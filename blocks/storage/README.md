# Storage Block

File upload and storage with S3 or local filesystem backends, image resizing via Pillow, and signed URL generation.

**Triggers**: upload, file, storage, s3, image, attachment, media, document

**Env vars**:
| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | — | AWS access key (S3 backend) |
| `AWS_SECRET_ACCESS_KEY` | — | AWS secret key (S3 backend) |
| `AWS_REGION` | `us-east-1` | AWS region |
| `S3_BUCKET` | — | S3 bucket name |
| `STORAGE_BACKEND` | `local` | Backend: `local` or `s3` |

**API endpoints**: `/api/storage/upload`, `/api/storage/files`, `/api/storage/files/{id}`, `/api/storage/upload/image`

**Dependencies**: `pip: boto3>=1.34.0, Pillow>=10.0.0, python-multipart>=0.0.9`
