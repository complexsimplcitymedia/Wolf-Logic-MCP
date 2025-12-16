# DNS Configuration Guide

## Prerequisites
- AWS CLI installed and configured
- Route 53 hosted zone created
- Domain registered with AWS Route 53

## Steps to Configure DNS

1. **Verify Hosted Zone**
   - Hosted Zone ID: Z02740683KP2RG209A02T
   - Domain: complexsimplicity.org

2. **Configure Nameservers**
   ```
   ns-2023.awsdns-60.co.uk
   ns-1257.awsdns-29.org
   ns-383.awsdns-47.com
   ns-936.awsdns-53.net
   ```

3. **Update DNS Records**
   ```bash
   chmod +x update-dns.sh
   ./update-dns.sh
   ```

4. **Verify Configuration**
   ```bash
   dig complexsimplicity.org NS
   dig complexsimplicity.org A
   dig www.complexsimplicity.org CNAME
   ```

## DNS Record Details

1. **NS Records**
   - Points to AWS Route 53 nameservers
   - TTL: 172800 seconds (48 hours)

2. **A Record (Apex Domain)**
   - Points to Netlify's load balancer
   - Uses ALIAS record for better performance

3. **CNAME Record (www subdomain)**
   - Points to Netlify app domain
   - TTL: 300 seconds (5 minutes)

## Troubleshooting

1. **DNS Propagation**
   - Changes may take up to 48 hours to propagate
   - Use `dig` or online DNS tools to check status

2. **SSL/HTTPS**
   - Netlify handles SSL certificate automatically
   - No additional configuration needed

3. **Common Issues**
   - Verify nameservers are correctly set
   - Check for conflicting DNS records
   - Ensure Netlify domain settings are correct