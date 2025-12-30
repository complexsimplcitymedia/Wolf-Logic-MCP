# Portainer SSO Configuration

## OAuth Configuration in Portainer UI

1. Access Portainer: http://100.110.82.181:9443
2. Navigate to Settings → Authentication
3. Select "OAuth" as authentication method
4. Select "Custom" as OAuth provider
5. Configure the following:

### OAuth Settings

**Client ID:** `portainer`

**Client Secret:** `vvkfAuPptmtraHU1bbOF6N6zZSFHMOeCr8vLhf9yrAhctQaCF5BCFDzWkGFMAlEb6OpS5cDf8hmCIJUxlmA9NXZzoxrd6hEyE4n043YtYUs4knzP7oa2BDgkWIVzmWxV`

**Authorization URL:** `http://100.110.82.181:9080/application/o/authorize/`

**Access Token URL:** `http://100.110.82.181:9080/application/o/token/`

**Resource URL (UserInfo):** `http://100.110.82.181:9080/application/o/userinfo/`

**Redirect URL:** `http://100.110.82.181:9443`

**Logout URL:** `http://100.110.82.181:9080/application/o/portainer/end-session/`

**User Identifier:** `sub` or `email`

**Scopes:** `openid profile email` (DO NOT use commas - Portainer shows commas by default but spaces are correct)

### Important Notes

- **Scopes:** Portainer UI may show commas between scopes, but you should use SPACES instead: `openid profile email`
- Make sure to save the configuration
- Test the OAuth login before logging out of your admin session

## Verification

After configuration:
1. Open incognito/private window
2. Navigate to http://100.110.82.181:9443
3. Click "OAuth login" or similar button
4. Should redirect to Authentik for authentication
5. After Authentik login, should redirect back to Portainer
