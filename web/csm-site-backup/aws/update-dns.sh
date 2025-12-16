#!/bin/bash

# Configuration
HOSTED_ZONE_ID="Z02740683KP2RG209A02T"

# Update DNS records
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch file://route53-config.json

echo "DNS records updated successfully!"
echo "Please note it may take up to 48 hours for DNS changes to fully propagate."