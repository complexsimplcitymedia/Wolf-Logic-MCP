## DNS Configuration Guide

1. **Route 53 Hosted Zone Setup**:
   - Go to Route 53 console
   - Create or select your hosted zone for `complexsimplicityai.com`
   - Note the nameservers assigned to your hosted zone

2. **Domain Registrar Configuration**:
   - Update nameservers at your domain registrar to use Route 53 nameservers
   - Wait 24-48 hours for DNS propagation

3. **Record Configuration**:
   - Create an A record for apex domain (complexsimplicityai.com)
   - Create an A record for www subdomain
   - Both should be Alias records pointing to your CloudFront distribution

4. **SSL Certificate Validation**:
   - Add CNAME records for SSL certificate validation
   - Wait for certificate validation to complete

5. **DNS Records**:
   ```
   Type  Name                     Value
   A     complexsimplicityai.com    ALIAS your-cloudfront-distribution.cloudfront.net
   A     www.complexsimplicityai.com ALIAS your-cloudfront-distribution.cloudfront.net
   ```

6. **Verification**:
   - Use `dig` or `nslookup` to verify DNS propagation:
     ```bash
     dig complexsimplicityai.com
     dig www.complexsimplicityai.com
     ```
   - Check SSL certificate status in ACM console
   - Verify website accessibility via both domains

7. **Additional Records**:
   - MX records for email (if needed)
   - TXT records for domain verification
   - SPF records for email security

8. **Monitoring**:
   - Set up Route 53 health checks
   - Configure DNS query logging
   - Set up alerts for DNS failures