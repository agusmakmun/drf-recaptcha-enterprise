"""
reCAPTCHA Enterprise client implementation.
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Union

from google.cloud import recaptchaenterprise_v1
from google.cloud.recaptchaenterprise_v1 import Assessment, Event
from google.oauth2 import service_account

from django.conf import settings

logger = logging.getLogger(__name__)


def load_credentials_from_file(
    credentials_path: str,
) -> Optional[service_account.Credentials]:
    """
    Load Google Cloud credentials from a service account key file.

    Args:
        credentials_path: Path to the service account JSON file

    Returns:
        Service account credentials if successful, None otherwise
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )
        logger.info(f"Successfully loaded credentials from: {credentials_path}")
        return credentials
    except Exception as e:
        logger.error(f"Failed to load credentials from {credentials_path}: {e}")
        return None


def extract_project_id_from_credentials(credentials_path: str) -> Optional[str]:
    """
    Extract project ID from Google Cloud credentials file.
    Supports both service account keys and OAuth client credentials.

    Args:
        credentials_path: Path to the credentials JSON file

    Returns:
        Project ID if found, None otherwise
    """
    try:
        with open(credentials_path, "r") as f:
            credentials = json.load(f)

            # Check for service account key format
            if credentials.get("type") == "service_account":
                project_id = credentials.get("project_id")
                if project_id:
                    logger.info(
                        f"Extracted project ID from service account: {project_id}"
                    )
                    return str(project_id)

            # Check for OAuth client credentials format
            elif "web" in credentials or "installed" in credentials:
                # OAuth client credentials have project_id nested in web/installed
                project_id = None
                if "web" in credentials:
                    project_id = credentials["web"].get("project_id")
                elif "installed" in credentials:
                    project_id = credentials["installed"].get("project_id")

                if project_id:
                    logger.info(
                        f"Extracted project ID from OAuth client credentials: {project_id}"
                    )
                    logger.warning(
                        "OAuth client credentials detected. For reCAPTCHA Enterprise, "
                        "you need a service account key file. This file can be used "
                        "to identify the project, but authentication will fail."
                    )
                    return str(project_id)

            # Generic fallback - look for project_id anywhere
            project_id = credentials.get("project_id")
            if project_id:
                logger.info(f"Extracted project ID from credentials: {project_id}")
                return str(project_id)

            logger.warning(
                f"No project_id found in credentials file: {credentials_path}"
            )
            return None

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to extract project ID from credentials: {e}")
        return None


def get_project_id() -> str:
    """
    Get the Google Cloud project ID from various sources.

    Returns:
        Project ID string

    Raises:
        ValueError: If project ID cannot be determined
    """
    # First, try to get from GOOGLE_APPLICATION_CREDENTIALS
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path and os.path.exists(credentials_path):
        project_id = extract_project_id_from_credentials(credentials_path)
        if project_id:
            return str(project_id)

    # Fallback to Django settings (for backward compatibility)
    project_id = getattr(settings, "RECAPTCHA_ENTERPRISE_PROJECT_ID", None)
    if project_id:
        logger.info(f"Using project ID from Django settings: {project_id}")
        return str(project_id)

    # Try to get from gcloud config
    try:
        import subprocess

        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            project_id = result.stdout.strip()
            logger.info(f"Using project ID from gcloud config: {project_id}")
            return str(project_id)
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass

    raise ValueError(
        "Could not determine Google Cloud project ID. "
        "Please set RECAPTCHA_ENTERPRISE_PROJECT_ID in Django settings, "
        "or ensure GOOGLE_APPLICATION_CREDENTIALS points to a valid service account file, "
        "or run 'gcloud config set project YOUR_PROJECT_ID'"
    )


def check_google_cloud_authentication() -> Dict[str, Any]:
    """
    Check Google Cloud authentication status and return information about the configuration.

    Returns:
        Dict containing authentication status and configuration details
    """
    result: Dict[str, Any] = {
        "authenticated": False,
        "method": None,
        "credentials_path": None,
        "error": None,
        "project_id": None,
    }

    try:
        # Check if GOOGLE_APPLICATION_CREDENTIALS is set
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if credentials_path:
            result["method"] = "service_account"
            result["credentials_path"] = credentials_path

            if os.path.exists(credentials_path):
                result["authenticated"] = True
                logger.info(f"Service account credentials found: {credentials_path}")
            else:
                result["error"] = f"Credentials file not found: {credentials_path}"
                logger.error(result["error"])
        else:
            result["method"] = "application_default_credentials"
            logger.info("Using Application Default Credentials (ADC)")

            # Try to initialize a client to test ADC
            try:
                recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()
                result["authenticated"] = True
                logger.info("Application Default Credentials are working")
            except Exception as e:
                result["error"] = f"ADC authentication failed: {str(e)}"
                logger.error(result["error"])

        # Get project ID from various sources
        try:
            result["project_id"] = get_project_id()
        except ValueError as e:
            result["error"] = f"Project ID detection failed: {str(e)}"
            logger.error(result["error"])
        except Exception:
            result["project_id"] = None

    except Exception as e:
        result["error"] = f"Authentication check failed: {str(e)}"
        logger.error(result["error"])

    return result


class ReCaptchaEnterpriseClient:
    """
    Client for interacting with Google reCAPTCHA Enterprise API.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        site_key: Optional[str] = None,
        credentials: Optional[Union[str, service_account.Credentials]] = None,
    ):
        """
        Initialize the reCAPTCHA Enterprise client.

        Args:
            project_id: Google Cloud project ID. If not provided, will be
                       automatically detected from credentials or Django settings.
            site_key: reCAPTCHA site key. If not provided, will use
                     RECAPTCHA_ENTERPRISE_SITE_KEY from Django settings.
            credentials: Google Cloud credentials. Can be:
                        - Path to service account key file (str)
                        - Service account credentials object
                        - None (uses GOOGLE_APPLICATION_CREDENTIALS or ADC)
        """
        # Handle credentials
        self.credentials = self._process_credentials(credentials)

        # Get project ID from various sources
        if project_id:
            self.project_id = project_id
        else:
            try:
                self.project_id = get_project_id()
            except ValueError as e:
                raise ValueError(f"Could not determine project ID: {e}")

        self.site_key = site_key or getattr(
            settings, "RECAPTCHA_ENTERPRISE_SITE_KEY", None
        )

        if not self.site_key:
            raise ValueError(
                "RECAPTCHA_ENTERPRISE_SITE_KEY must be set in Django settings"
            )

        # Check authentication status
        self._check_authentication()

        # Initialize the reCAPTCHA Enterprise client
        try:
            if self.credentials:
                self.client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient(
                    credentials=self.credentials
                )
                logger.info(
                    "Initialized reCAPTCHA Enterprise client with provided credentials"
                )
            else:
                self.client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()
                logger.info(
                    "Initialized reCAPTCHA Enterprise client with default credentials"
                )

            self.project_path = f"projects/{self.project_id}"
        except Exception as e:
            logger.error(f"Failed to initialize reCAPTCHA Enterprise client: {str(e)}")
            raise ValueError(
                "Failed to initialize reCAPTCHA Enterprise client. "
                "Please provide valid credentials or ensure GOOGLE_APPLICATION_CREDENTIALS is set"
            )

    def _process_credentials(
        self, credentials: Optional[Union[str, service_account.Credentials]]
    ) -> Optional[service_account.Credentials]:
        """
        Process credentials parameter and return service account credentials.

        Args:
            credentials: Can be a file path (str) or credentials object

        Returns:
            Service account credentials or None
        """
        if credentials is None:
            return None

        if isinstance(credentials, str):
            # It's a file path
            if not os.path.exists(credentials):
                raise ValueError(f"Credentials file not found: {credentials}")

            # Check if it's a service account file
            try:
                with open(credentials, "r") as f:
                    cred_data = json.load(f)
                    if cred_data.get("type") != "service_account":
                        raise ValueError(
                            f"File {credentials} is not a service account key file. "
                            f"Found type: {cred_data.get('type', 'unknown')}"
                        )
            except (json.JSONDecodeError, KeyError) as e:
                raise ValueError(f"Invalid credentials file format: {e}")

            # Load the credentials
            return load_credentials_from_file(credentials)

        elif isinstance(credentials, service_account.Credentials):
            # It's already a credentials object
            return credentials

        else:
            raise ValueError(
                f"Invalid credentials type: {type(credentials)}. "
                f"Expected str (file path) or service_account.Credentials"
            )

    def _check_authentication(self) -> None:
        """Check if Google Cloud authentication is properly configured."""
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if credentials_path:
            if not os.path.exists(credentials_path):
                logger.warning(
                    f"GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {credentials_path}"
                )
                raise ValueError(
                    f"GOOGLE_APPLICATION_CREDENTIALS file not found: {credentials_path}. "
                    "Please check the file path or run 'gcloud auth application-default login'"
                )
            logger.info(f"Using service account credentials from: {credentials_path}")
        else:
            logger.info(
                "GOOGLE_APPLICATION_CREDENTIALS not set. "
                "Using Application Default Credentials (ADC). "
                "Run 'gcloud auth application-default login' if needed."
            )

    def create_assessment(
        self,
        token: str,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        expected_action: Optional[str] = None,
    ) -> Assessment:
        """
        Create an assessment for the given reCAPTCHA token.

        Args:
            token: The reCAPTCHA token from the frontend
            user_ip: The user's IP address
            user_agent: The user's user agent string
            expected_action: The expected action name (if using action-based scoring)

        Returns:
            Assessment object from the reCAPTCHA Enterprise API

        Raises:
            Exception: If the assessment creation fails
        """
        try:
            # Create the event
            event = Event()
            event.site_key = self.site_key
            event.token = token

            if user_ip:
                event.user_ip_address = user_ip

            if user_agent:
                event.user_agent = user_agent

            if expected_action:
                event.expected_action = expected_action

            # Create the assessment request
            request = recaptchaenterprise_v1.CreateAssessmentRequest()
            request.parent = self.project_path
            request.assessment = Assessment()
            request.assessment.event = event

            # Make the API call
            response = self.client.create_assessment(request=request)

            logger.info(
                f"reCAPTCHA assessment created successfully. "
                f"Score: {response.risk_analysis.score}"
            )

            return response

        except Exception as e:
            logger.error(f"Failed to create reCAPTCHA assessment: {str(e)}")
            raise

    def verify_token(
        self,
        token: str,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        expected_action: Optional[str] = None,
        min_score: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Verify a reCAPTCHA token and return verification results.

        Args:
            token: The reCAPTCHA token from the frontend
            user_ip: The user's IP address
            user_agent: The user's user agent string
            expected_action: The expected action name (if using action-based scoring)
            min_score: Minimum score threshold for verification (0.0 to 1.0)

        Returns:
            Dictionary containing verification results:
            {
                'success': bool,
                'score': float,
                'action': str,
                'error_codes': list,
                'assessment': Assessment object
            }
        """
        try:
            assessment = self.create_assessment(
                token=token,
                user_ip=user_ip,
                user_agent=user_agent,
                expected_action=expected_action,
            )

            # Extract results
            risk_analysis = assessment.risk_analysis
            score = risk_analysis.score
            reasons = list(risk_analysis.reasons)

            # Check if the score meets the minimum threshold
            success = score >= min_score

            # Check action if provided
            action_valid = True
            if expected_action and assessment.token_properties:
                action_valid = assessment.token_properties.action == expected_action

            success = success and action_valid

            return {
                "success": success,
                "score": score,
                "action": (
                    assessment.token_properties.action
                    if assessment.token_properties
                    else None
                ),
                "error_codes": reasons,
                "assessment": assessment,
                "valid": (
                    assessment.token_properties.valid
                    if assessment.token_properties
                    else False
                ),
                "hostname": (
                    assessment.token_properties.hostname
                    if assessment.token_properties
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"reCAPTCHA verification failed: {str(e)}")
            return {
                "success": False,
                "score": 0.0,
                "action": None,
                "error_codes": ["VERIFICATION_FAILED"],
                "assessment": None,
                "valid": False,
                "hostname": None,
                "error": str(e),
            }
