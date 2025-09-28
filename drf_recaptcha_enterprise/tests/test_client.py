"""
Unit tests for client.py module.
"""

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from drf_recaptcha_enterprise.client import (
    ReCaptchaEnterpriseClient,
    check_google_cloud_authentication,
    extract_project_id_from_credentials,
    get_project_id,
    load_credentials_from_file,
)
from drf_recaptcha_enterprise.tests.conftest import create_mock_assessment


class TestLoadCredentialsFromFile:
    """Test load_credentials_from_file function."""

    def test_load_credentials_success(self, temp_credentials_file):
        """Test successful credentials loading."""
        with patch(
            "drf_recaptcha_enterprise.client.service_account.Credentials.from_service_account_file"
        ) as mock_from_file:
            mock_credentials = Mock()
            mock_from_file.return_value = mock_credentials

            result = load_credentials_from_file(temp_credentials_file)

            assert result == mock_credentials
            mock_from_file.assert_called_once_with(temp_credentials_file)

    def test_load_credentials_file_not_found(self):
        """Test credentials loading with non-existent file."""
        result = load_credentials_from_file("/non/existent/file.json")
        assert result is None

    def test_load_credentials_exception(self, temp_credentials_file):
        """Test credentials loading with exception."""
        with patch(
            "drf_recaptcha_enterprise.client.service_account.Credentials.from_service_account_file"
        ) as mock_from_file:
            mock_from_file.side_effect = Exception("Test exception")

            result = load_credentials_from_file(temp_credentials_file)
            assert result is None


class TestExtractProjectIdFromCredentials:
    """Test extract_project_id_from_credentials function."""

    def test_extract_project_id_service_account(self, temp_credentials_file):
        """Test extracting project ID from service account credentials."""
        result = extract_project_id_from_credentials(temp_credentials_file)
        assert result == "test-project-id"

    def test_extract_project_id_oauth_web(self):
        """Test extracting project ID from OAuth web credentials."""
        credentials_data = {
            "web": {
                "project_id": "oauth-web-project",
                "client_id": "test-client-id",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(credentials_data, f)
            temp_file = f.name

        try:
            result = extract_project_id_from_credentials(temp_file)
            assert result == "oauth-web-project"
        finally:
            os.unlink(temp_file)

    def test_extract_project_id_oauth_installed(self):
        """Test extracting project ID from OAuth installed credentials."""
        credentials_data = {
            "installed": {
                "project_id": "oauth-installed-project",
                "client_id": "test-client-id",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(credentials_data, f)
            temp_file = f.name

        try:
            result = extract_project_id_from_credentials(temp_file)
            assert result == "oauth-installed-project"
        finally:
            os.unlink(temp_file)

    def test_extract_project_id_generic_fallback(self):
        """Test extracting project ID using generic fallback."""
        credentials_data = {
            "project_id": "generic-project",
            "type": "some_other_type",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(credentials_data, f)
            temp_file = f.name

        try:
            result = extract_project_id_from_credentials(temp_file)
            assert result == "generic-project"
        finally:
            os.unlink(temp_file)

    def test_extract_project_id_no_project_id(self):
        """Test extracting project ID when none exists."""
        credentials_data = {
            "type": "service_account",
            "client_id": "test-client-id",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(credentials_data, f)
            temp_file = f.name

        try:
            result = extract_project_id_from_credentials(temp_file)
            assert result is None
        finally:
            os.unlink(temp_file)

    def test_extract_project_id_invalid_json(self):
        """Test extracting project ID from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name

        try:
            result = extract_project_id_from_credentials(temp_file)
            assert result is None
        finally:
            os.unlink(temp_file)

    def test_extract_project_id_file_not_found(self):
        """Test extracting project ID from non-existent file."""
        result = extract_project_id_from_credentials("/non/existent/file.json")
        assert result is None


class TestGetProjectId:
    """Test get_project_id function."""

    def test_get_project_id_from_credentials_env(self, temp_credentials_file):
        """Test getting project ID from GOOGLE_APPLICATION_CREDENTIALS."""
        with patch.dict(
            os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": temp_credentials_file}
        ):
            result = get_project_id()
            assert result == "test-project-id"

    def test_get_project_id_from_django_settings(self):
        """Test getting project ID from Django settings."""
        with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
            mock_settings.RECAPTCHA_ENTERPRISE_PROJECT_ID = "django-project-id"

            with patch.dict(os.environ, {}, clear=True):
                result = get_project_id()
                assert result == "django-project-id"

    def test_get_project_id_from_gcloud_config(self):
        """Test getting project ID from gcloud config."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "gcloud-project-id\n"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = mock_result

            with patch.dict(os.environ, {}, clear=True):
                with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                    mock_settings.RECAPTCHA_ENTERPRISE_PROJECT_ID = None

                    result = get_project_id()
                    assert result == "gcloud-project-id"

    def test_get_project_id_no_sources(self):
        """Test getting project ID when no sources are available."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_PROJECT_ID = None

                with patch("subprocess.run") as mock_run:
                    mock_run.side_effect = FileNotFoundError()

                    with pytest.raises(
                        ValueError, match="Could not determine Google Cloud project ID"
                    ):
                        get_project_id()


class TestCheckGoogleCloudAuthentication:
    """Test check_google_cloud_authentication function."""

    def test_check_authentication_with_credentials_file(self, temp_credentials_file):
        """Test authentication check with credentials file."""
        with patch.dict(
            os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": temp_credentials_file}
        ):
            result = check_google_cloud_authentication()

            assert result["authenticated"] is True
            assert result["method"] == "service_account"
            assert result["credentials_path"] == temp_credentials_file
            assert result["project_id"] == "test-project-id"
            assert result["error"] is None

    def test_check_authentication_credentials_file_not_found(self):
        """Test authentication check with non-existent credentials file."""
        with patch.dict(
            os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/non/existent/file.json"}
        ):
            result = check_google_cloud_authentication()

            assert result["authenticated"] is False
            assert result["method"] == "service_account"
            assert result["credentials_path"] == "/non/existent/file.json"
            assert "Credentials file not found" in result["error"]

    def test_check_authentication_adc_success(self):
        """Test authentication check with successful ADC."""
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
            ) as mock_client:
                mock_client.return_value = Mock()

                result = check_google_cloud_authentication()

                assert result["authenticated"] is True
                assert result["method"] == "application_default_credentials"
                assert result["error"] is None

    def test_check_authentication_adc_failure(self):
        """Test authentication check with failed ADC."""
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
            ) as mock_client:
                mock_client.side_effect = Exception("ADC failed")

                result = check_google_cloud_authentication()

                assert result["authenticated"] is False
                assert result["method"] == "application_default_credentials"
                assert "ADC authentication failed" in result["error"]

    def test_check_authentication_project_id_failure(self):
        """Test authentication check with project ID detection failure."""
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "drf_recaptcha_enterprise.client.get_project_id"
            ) as mock_get_project_id:
                mock_get_project_id.side_effect = ValueError("Project ID failed")

                result = check_google_cloud_authentication()

                assert "Project ID detection failed" in result["error"]


class TestReCaptchaEnterpriseClient:
    """Test ReCaptchaEnterpriseClient class."""

    def test_init_with_all_parameters(self):
        """Test client initialization with all parameters."""
        from google.oauth2 import service_account

        mock_credentials = Mock(spec=service_account.Credentials)

        with patch(
            "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
        ) as mock_client:
            mock_client.return_value = Mock()

            client = ReCaptchaEnterpriseClient(
                project_id="test-project",
                site_key="test-site-key",
                credentials=mock_credentials,
            )

            assert client.project_id == "test-project"
            assert client.site_key == "test-site-key"
            assert client.credentials == mock_credentials

    def test_init_with_django_settings(self):
        """Test client initialization using Django settings."""
        with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
            mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "settings-site-key"
            mock_settings.RECAPTCHA_ENTERPRISE_PROJECT_ID = "settings-project-id"

            with patch(
                "drf_recaptcha_enterprise.client.get_project_id"
            ) as mock_get_project_id:
                mock_get_project_id.return_value = "settings-project-id"

                with patch(
                    "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
                ) as mock_client:
                    mock_client.return_value = Mock()

                    client = ReCaptchaEnterpriseClient()

                    assert client.project_id == "settings-project-id"
                    assert client.site_key == "settings-site-key"

    def test_init_missing_site_key(self):
        """Test client initialization with missing site key."""
        with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
            mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = None

            with patch(
                "drf_recaptcha_enterprise.client.get_project_id"
            ) as mock_get_project_id:
                mock_get_project_id.return_value = "test-project"

                with pytest.raises(
                    ValueError, match="RECAPTCHA_ENTERPRISE_SITE_KEY must be set"
                ):
                    ReCaptchaEnterpriseClient()

    def test_init_missing_project_id(self):
        """Test client initialization with missing project ID."""
        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.side_effect = ValueError("No project ID")

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with pytest.raises(ValueError, match="Could not determine project ID"):
                    ReCaptchaEnterpriseClient()

    def test_init_client_creation_failure(self):
        """Test client initialization with client creation failure."""
        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.return_value = "test-project"

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with patch(
                    "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
                ) as mock_client:
                    mock_client.side_effect = Exception("Client creation failed")

                    with pytest.raises(
                        ValueError,
                        match="Failed to initialize reCAPTCHA Enterprise client",
                    ):
                        ReCaptchaEnterpriseClient()

    def test_process_credentials_string_path(self, temp_credentials_file):
        """Test processing credentials as string path."""
        with patch(
            "drf_recaptcha_enterprise.client.load_credentials_from_file"
        ) as mock_load:
            mock_credentials = Mock()
            mock_load.return_value = mock_credentials

            with patch(
                "drf_recaptcha_enterprise.client.get_project_id"
            ) as mock_get_project_id:
                mock_get_project_id.return_value = "test-project"

                with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                    mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                    with patch(
                        "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
                    ) as mock_client:
                        mock_client.return_value = Mock()

                        client = ReCaptchaEnterpriseClient(
                            credentials=temp_credentials_file
                        )

                        assert client.credentials == mock_credentials
                        mock_load.assert_called_once_with(temp_credentials_file)

    def test_process_credentials_credentials_object(self):
        """Test processing credentials as credentials object."""
        from google.oauth2 import service_account

        mock_credentials = Mock(spec=service_account.Credentials)

        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.return_value = "test-project"

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with patch(
                    "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
                ) as mock_client:
                    mock_client.return_value = Mock()

                    client = ReCaptchaEnterpriseClient(credentials=mock_credentials)

                    assert client.credentials == mock_credentials

    def test_process_credentials_none(self):
        """Test processing credentials as None."""
        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.return_value = "test-project"

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with patch(
                    "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
                ) as mock_client:
                    mock_client.return_value = Mock()

                    client = ReCaptchaEnterpriseClient(credentials=None)

                    assert client.credentials is None

    def test_process_credentials_invalid_type(self):
        """Test processing credentials with invalid type."""
        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.return_value = "test-project"

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with pytest.raises(ValueError, match="Invalid credentials type"):
                    ReCaptchaEnterpriseClient(credentials=123)

    def test_process_credentials_file_not_found(self):
        """Test processing credentials with non-existent file."""
        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.return_value = "test-project"

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with pytest.raises(ValueError, match="Credentials file not found"):
                    ReCaptchaEnterpriseClient(credentials="/non/existent/file.json")

    def test_process_credentials_invalid_service_account(self):
        """Test processing credentials with invalid service account file."""
        invalid_credentials_data = {
            "type": "oauth",
            "project_id": "test-project-id",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_credentials_data, f)
            temp_file = f.name

        try:
            with patch(
                "drf_recaptcha_enterprise.client.get_project_id"
            ) as mock_get_project_id:
                mock_get_project_id.return_value = "test-project"

                with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                    mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                    with pytest.raises(
                        ValueError, match="is not a service account key file"
                    ):
                        ReCaptchaEnterpriseClient(credentials=temp_file)
        finally:
            os.unlink(temp_file)

    def test_create_assessment_success(self, mock_assessment):
        """Test successful assessment creation."""
        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.return_value = "test-project"

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with patch(
                    "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
                ) as mock_client_class:
                    mock_client = Mock()
                    mock_client.create_assessment.return_value = mock_assessment
                    mock_client_class.return_value = mock_client

                    client = ReCaptchaEnterpriseClient()
                    result = client.create_assessment(
                        token="test-token",
                        user_ip="192.168.1.1",
                        user_agent="Test Agent",
                        expected_action="submit",
                    )

                    assert result == mock_assessment
                    mock_client.create_assessment.assert_called_once()

    def test_create_assessment_failure(self):
        """Test assessment creation failure."""
        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.return_value = "test-project"

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with patch(
                    "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
                ) as mock_client_class:
                    mock_client = Mock()
                    mock_client.create_assessment.side_effect = Exception("API Error")
                    mock_client_class.return_value = mock_client

                    client = ReCaptchaEnterpriseClient()

                    with pytest.raises(Exception, match="API Error"):
                        client.create_assessment(token="test-token")

    def test_verify_token_success(self, sample_verification_result):
        """Test successful token verification."""
        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.return_value = "test-project"

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with patch(
                    "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
                ) as mock_client_class:
                    mock_client = Mock()
                    mock_assessment = create_mock_assessment(
                        score=0.8, valid=True, action="submit"
                    )
                    mock_client.create_assessment.return_value = mock_assessment
                    mock_client_class.return_value = mock_client

                    client = ReCaptchaEnterpriseClient()
                    result = client.verify_token(
                        token="test-token",
                        user_ip="192.168.1.1",
                        user_agent="Test Agent",
                        expected_action="submit",
                        min_score=0.5,
                    )

                    assert result["success"] is True
                    assert result["score"] == 0.8
                    assert result["action"] == "submit"
                    assert result["valid"] is True

    def test_verify_token_low_score(self):
        """Test token verification with low score."""
        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.return_value = "test-project"

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with patch(
                    "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
                ) as mock_client_class:
                    mock_client = Mock()
                    mock_assessment = create_mock_assessment(
                        score=0.2, valid=True, action="submit"
                    )
                    mock_client.create_assessment.return_value = mock_assessment
                    mock_client_class.return_value = mock_client

                    client = ReCaptchaEnterpriseClient()
                    result = client.verify_token(token="test-token", min_score=0.5)

                    assert result["success"] is False
                    assert result["score"] == 0.2

    def test_verify_token_invalid_action(self):
        """Test token verification with invalid action."""
        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.return_value = "test-project"

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with patch(
                    "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
                ) as mock_client_class:
                    mock_client = Mock()
                    mock_assessment = create_mock_assessment(
                        score=0.8, valid=True, action="wrong_action"
                    )
                    mock_client.create_assessment.return_value = mock_assessment
                    mock_client_class.return_value = mock_client

                    client = ReCaptchaEnterpriseClient()
                    result = client.verify_token(
                        token="test-token", expected_action="submit", min_score=0.5
                    )

                    assert result["success"] is False
                    assert result["score"] == 0.8

    def test_verify_token_exception(self):
        """Test token verification with exception."""
        with patch(
            "drf_recaptcha_enterprise.client.get_project_id"
        ) as mock_get_project_id:
            mock_get_project_id.return_value = "test-project"

            with patch("drf_recaptcha_enterprise.client.settings") as mock_settings:
                mock_settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"

                with patch(
                    "drf_recaptcha_enterprise.client.recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient"
                ) as mock_client_class:
                    mock_client = Mock()
                    mock_client.create_assessment.side_effect = Exception("API Error")
                    mock_client_class.return_value = mock_client

                    client = ReCaptchaEnterpriseClient()
                    result = client.verify_token(token="test-token")

                    assert result["success"] is False
                    assert result["score"] == 0.0
                    assert result["error_codes"] == ["VERIFICATION_FAILED"]
                    assert "API Error" in result["error"]
