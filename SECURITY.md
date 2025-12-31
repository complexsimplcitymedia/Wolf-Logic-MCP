# Security Policy

## Supported Versions

Wolf Logic MCP is actively maintained on the `main` branch. We recommend always using the latest version.

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| feature branches | :x:      |

## Reporting a Vulnerability

If you discover a security vulnerability in Wolf Logic MCP, please report it responsibly:

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. **Email**: Send details to the repository maintainer via GitHub's private vulnerability reporting feature, or contact through the repository owner's profile
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

### Response Timeline

- **Initial Response**: Within 48 hours of report
- **Assessment**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: Within 24-48 hours
  - High: Within 7 days
  - Medium: Within 30 days
  - Low: Next release cycle

### What to Expect

- Acknowledgment of your report
- Regular updates on fix progress
- Credit in the security advisory (unless you prefer anonymity)
- Notification when the fix is released

## Security Considerations

This project handles:
- Database connections (PostgreSQL on Tailscale network)
- API keys and credentials (stored in environment variables)
- MCP server communications

### Best Practices for Deployment

1. Never commit `.env` files or credentials
2. Use Tailscale for internal network communication
3. Ensure PostgreSQL connections use SSL/TLS
4. Regularly rotate API keys
5. Monitor access logs for suspicious activity
