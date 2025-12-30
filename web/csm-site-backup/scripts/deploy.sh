#!/bin/bash

# Configuration
BUCKET_NAME="complexsimplicity.org"
DISTRIBUTION_ID="YOUR_CLOUDFRONT_DISTRIBUTION_ID"
REGION="us-east-1"

# Build the project
echo "Building project..."
npm run build

# Sync built files to S3
echo "Uploading to S3..."
aws s3 sync dist/ s3://$BUCKET_NAME \
  --delete \
  --cache-control "max-age=31536000,public" \
  --exclude "*.html" \
  --region $REGION

# Upload HTML files with different cache settings
echo "Uploading HTML files..."
aws s3 sync dist/ s3://$BUCKET_NAME \
  --delete \
  --cache-control "no-cache" \
  --exclude "*" \
  --include "*.html" \
  --region $REGION

# Invalidate CloudFront cache
echo "Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

echo "Deployment complete!"