#!/usr/bin/env python3
"""
Authentik API Client for Wolf AI
Handles user provisioning and MFA enforcement
"""

import requests
import logging
import os
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthentikClient:
    def __init__(self, base_url=None, api_token=None):
        """Initialize Authentik API client"""
        self.base_url = base_url or os.getenv("AUTHENTIK_URL", "http://100.110.82.181:9000")
        self.api_token = api_token or os.getenv("AUTHENTIK_API_TOKEN", "")
        self.api_url = f"{self.base_url}/api/v3"

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def create_user(self, username: str, email: str, phone: str) -> Optional[str]:
        """
        Create user in Authentik with MFA requirement

        Returns:
            authentik_user_id or None if failed
        """
        try:
            payload = {
                "username": username,
                "name": username,
                "email": email,
                "is_active": True,
                "path": "users",
                "attributes": {
                    "phone": phone,
                    "mfa_required": True,
                    "mfa_enrolled": False
                }
            }

            response = requests.post(
                f"{self.api_url}/core/users/",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()

            user_data = response.json()
            user_id = user_data.get('pk')

            logger.info(f"Authentik user created: {username} (ID: {user_id})")
            return str(user_id)

        except requests.exceptions.HTTPError as e:
            logger.error(f"Failed to create Authentik user: {e}")
            logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Authentik user creation error: {e}")
            return None

    def add_user_to_group(self, user_id: str, group_name: str = "beta-users") -> bool:
        """Add user to Authentik group"""
        try:
            # Get group ID
            response = requests.get(
                f"{self.api_url}/core/groups/",
                headers=self.headers,
                params={"name": group_name}
            )
            response.raise_for_status()

            groups = response.json().get('results', [])
            if not groups:
                logger.warning(f"Group '{group_name}' not found")
                return False

            group_id = groups[0]['pk']

            # Add user to group
            response = requests.post(
                f"{self.api_url}/core/groups/{group_id}/add_user/",
                headers=self.headers,
                json={"pk": user_id}
            )
            response.raise_for_status()

            logger.info(f"User {user_id} added to group '{group_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to add user to group: {e}")
            return False

    def check_mfa_status(self, user_id: str) -> Dict[str, Any]:
        """Check if user has configured MFA"""
        try:
            response = requests.get(
                f"{self.api_url}/authenticators/all/",
                headers=self.headers,
                params={"user": user_id}
            )
            response.raise_for_status()

            authenticators = response.json().get('results', [])

            has_totp = any(auth['type'] == 'totp' for auth in authenticators)
            has_webauthn = any(auth['type'] == 'webauthn' for auth in authenticators)

            return {
                "mfa_configured": len(authenticators) > 0,
                "totp_enabled": has_totp,
                "webauthn_enabled": has_webauthn,
                "authenticator_count": len(authenticators)
            }

        except Exception as e:
            logger.error(f"Failed to check MFA status: {e}")
            return {"mfa_configured": False}

    def create_mfa_enrollment_policy(self) -> bool:
        """
        Create policy that enforces MFA enrollment
        This policy binds to the default authentication flow
        """
        try:
            # Create expression policy
            policy_payload = {
                "name": "wolf-mfa-required",
                "execution_logging": True,
                "expression": """
# Require MFA enrollment for all users
# Check if user has any MFA device configured
from authentik.stages.authenticator_validate.models import Device

user_devices = Device.objects.filter(user=request.user, confirmed=True)

# If no MFA configured, deny access and redirect to enrollment
if user_devices.count() == 0:
    ak_message("MFA enrollment required. Please configure an authenticator.")
    return False

return True
                """
            }

            response = requests.post(
                f"{self.api_url}/policies/expression/",
                headers=self.headers,
                json=policy_payload
            )
            response.raise_for_status()

            policy_id = response.json().get('pk')
            logger.info(f"MFA enforcement policy created: {policy_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create MFA policy: {e}")
            return False

    def bind_mfa_policy_to_flow(self, flow_slug: str = "default-authentication-flow") -> bool:
        """Bind MFA enforcement policy to authentication flow"""
        try:
            # Get policy ID
            response = requests.get(
                f"{self.api_url}/policies/expression/",
                headers=self.headers,
                params={"name": "wolf-mfa-required"}
            )
            response.raise_for_status()

            policies = response.json().get('results', [])
            if not policies:
                logger.error("MFA policy not found")
                return False

            policy_id = policies[0]['pk']

            # Get flow ID
            response = requests.get(
                f"{self.api_url}/flows/instances/",
                headers=self.headers,
                params={"slug": flow_slug}
            )
            response.raise_for_status()

            flows = response.json().get('results', [])
            if not flows:
                logger.error(f"Flow '{flow_slug}' not found")
                return False

            flow_id = flows[0]['pk']

            # Create binding
            binding_payload = {
                "policy": policy_id,
                "target": flow_id,
                "enabled": True,
                "order": 0
            }

            response = requests.post(
                f"{self.api_url}/policies/bindings/",
                headers=self.headers,
                json=binding_payload
            )
            response.raise_for_status()

            logger.info(f"MFA policy bound to flow '{flow_slug}'")
            return True

        except Exception as e:
            logger.error(f"Failed to bind MFA policy: {e}")
            return False

    def generate_enrollment_link(self, user_id: str) -> Optional[str]:
        """Generate MFA enrollment link for user"""
        try:
            response = requests.post(
                f"{self.api_url}/core/users/{user_id}/recovery/",
                headers=self.headers
            )
            response.raise_for_status()

            recovery_data = response.json()
            enrollment_link = recovery_data.get('link')

            logger.info(f"MFA enrollment link generated for user {user_id}")
            return enrollment_link

        except Exception as e:
            logger.error(f"Failed to generate enrollment link: {e}")
            return None


def setup_authentik_mfa():
    """Initialize Authentik MFA enforcement (run once)"""
    client = AuthentikClient()

    logger.info("Setting up Authentik MFA enforcement...")

    # Create MFA policy
    if client.create_mfa_enrollment_policy():
        logger.info("✓ MFA policy created")

    # Bind to default auth flow
    if client.bind_mfa_policy_to_flow():
        logger.info("✓ MFA policy bound to authentication flow")

    logger.info("Authentik MFA enforcement configured")


if __name__ == "__main__":
    # Setup MFA enforcement
    setup_authentik_mfa()
