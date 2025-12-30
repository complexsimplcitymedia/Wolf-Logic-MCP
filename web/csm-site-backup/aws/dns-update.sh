#!/bin/bash

# Configuration
HOSTED_ZONE_ID="YOUR_HOSTED_ZONE_ID"
DOMAIN="complexsimplicity.org"
CLOUDFRONT_DOMAIN="YOUR_CLOUDFRONT_DISTRIBUTION_DOMAIN"

# Update DNS records
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch file://route53-records.json

# Verify DNS propagation
echo "Verifying DNS propagation..."
echo "This may take some time..."

check_dns() {
  local domain=$1
  dig +short $domain | grep cloudfront.net
}

# Wait for DNS propagation
for domain in "$DOMAIN" "www.$DOMAIN"; do
  echo "Checking $domain..."
  while ! check_dns $domain; do
    echo "Waiting for DNS propagation for $domain..."
    sleep 30
  done
  echo "$domain DNS propagated successfully!"
done

echo "DNS configuration complete!"