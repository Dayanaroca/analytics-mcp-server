import os
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Literal
from src.sdk.analytics_client import AnalyticsClient
from dotenv import load_dotenv
from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request
from urllib.parse import urlparse
from ipaddress import ip_address, ip_network, IPv4Network, IPv6Network

load_dotenv()


_current_account: ContextVar[str | None] = ContextVar("current_zoho_account", default=None)


@dataclass(frozen=True)
class ZohoAccount:
    key: str
    alias: str
    client_id: str | None
    client_secret: str | None
    refresh_token: str | None
    org_id: str
    analytics_server_url: str
    accounts_server_url: str | None


class Settings:

    @staticmethod
    def _get_accounts_url(project_domain: str) -> str:
        region_map = {
            ".zoho.in": "https://accounts.zoho.in",
            ".zoho.eu": "https://accounts.zoho.eu",
            ".zoho.com.au": "https://accounts.zoho.com.au",
            ".zoho.jp": "https://accounts.zoho.jp",
        }
        for suffix, url in region_map.items():
            if project_domain.endswith(suffix):
                return url
        return "https://accounts.zoho.com"

    @staticmethod
    def _normalize_server_url(url: str | None, default: str | None = None) -> str | None:
        value = url or default
        if not value:
            return None
        value = value.strip()
        if not value:
            return None
        if not value.startswith(("http://", "https://")):
            value = f"https://{value}"
        return value.rstrip("/")

    @classmethod
    def _analytics_domain(cls) -> str:
        return urlparse(cls.ANALYTICS_SERVER_URL).netloc

    @classmethod
    def accounts_server_url(cls) -> str:
        return cls._get_accounts_url(cls._analytics_domain())


    @classmethod
    def oidc_provider_base_url(cls) -> str:
        return cls.accounts_server_url()


    # General Settings
    ANALYTICS_SERVER_URL = os.getenv("ANALYTICS_SERVER_URL", "https://analyticsapi.zoho.com")

    ## Tools
    ANALYTICS_WORKSPACE_LIST_RESULT_SIZE = int(os.getenv("ANALYTICS_WORKSPACE_LIST_RESULT_SIZE") or 20)
    ANALYTICS_VIEW_LIST_RESULT_SIZE = int(os.getenv("ANALYTICS_VIEW_LIST_RESULT_SIZE") or 15)
    QUERY_DATA_RESULT_ROW_LIMITS = int(os.getenv("QUERY_DATA_RESULT_ROW_LIMITS") or 20)
    QUERY_DATA_POLLING_INTERVAL = int(os.getenv("QUERY_DATA_POLLING_INTERVAL") or 4)
    QUERY_DATA_QUEUE_TIMEOUT = int(os.getenv("QUERY_DATA_QUEUE_TIMEOUT") or 120)
    QUERY_DATA_QUERY_EXECUTION_TIMEOUT = int(os.getenv("QUERY_DATA_QUERY_EXECUTION_TIMEOUT") or 30)

    # Settings required for Local
    CLIENT_ID = os.getenv("ANALYTICS_CLIENT_ID")
    CLIENT_SECRET = os.getenv("ANALYTICS_CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("ANALYTICS_REFRESH_TOKEN")
    MCP_DATA_DIR = os.getenv("ANALYTICS_MCP_DATA_DIR")
    ORG_ID = os.getenv("ANALYTICS_ORG_ID", "-1")
    

    OIDC_PROVIDER_CLIENT_ID = os.getenv("OIDC_PROVIDER_CLIENT_ID")
    OIDC_PROVIDER_CLIENT_SECRET = os.getenv("OIDC_PROVIDER_CLIENT_SECRET")
    MCP_SERVER_PUBLIC_URL = os.getenv("MCP_SERVER_PUBLIC_URL")
    HOSTED_LOCATION = None # "LOCAL" or "REMOTE", set in startup
    SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "supersecretkey")
    PORT = int(os.getenv("PORT","4000"))
    MCP_SERVER_ORG_IDS = os.getenv("MCP_SERVER_ORG_IDS", "")
    BEHIND_PROXY = os.getenv("BEHIND_PROXY", "False").lower() == "true"
    TRUSTED_PROXY_LIST: list[IPv4Network | IPv6Network] = (
        [ip_network(ip.strip(), strict=False) 
         for ip in os.getenv("TRUSTED_PROXY_LIST", "").split(",") if ip.strip()]
        if BEHIND_PROXY else []
    )
    DEPLOYMENT_SCENARIO: Literal["private_network", "public_network"]  = os.getenv("DEPLOYMENT_SCENARIO", "private_network")
    _RAW_TRUSTED_IP_PATTERNS = [
        item.strip()
        for item in os.getenv("TRUSTED_PUBLIC_NETWORKS", "").split(",")
        if item.strip()
    ]

    _RAW_TRUSTED_DOMAIN_PATTERNS = [
        item.strip().lower()
        for item in os.getenv("TRUSTED_DOMAINS_ALLOWLIST", "").split(",")
        if item.strip()
    ]

    TRUSTED_IP_NETWORKS: list[IPv4Network | IPv6Network] = []
    TRUSTED_DOMAIN_PATTERNS = [
        re.compile(pattern) for pattern in _RAW_TRUSTED_DOMAIN_PATTERNS
    ]
    CLIENT_IP_HEADER: str = None if os.getenv("CLIENT_IP_HEADER") is None else os.getenv("CLIENT_IP_HEADER")

    if DEPLOYMENT_SCENARIO == "public_network":

        for pattern in _RAW_TRUSTED_IP_PATTERNS:
            try:
                # Parse as CIDR notation only
                TRUSTED_IP_NETWORKS.append(ip_network(pattern, strict=False))
            except ValueError as e:
                raise ValueError(
                    f"Invalid CIDR notation '{pattern}' in TRUSTED_PUBLIC_NETWORKS. "
                    f"Only CIDR notation (e.g., '192.168.1.0/24', '10.0.0.0/8') is supported. "
                    f"Error: {e}"
                )

        # Store domains as exact match strings (case-insensitive comparison will be done at check time)
        TRUSTED_DOMAINS = _RAW_TRUSTED_DOMAIN_PATTERNS

    ## Persistence Settings for Remote
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "memory").lower()
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")  

    # Catalyst Persistence Settings
    CATALYST_SDK_APP_NAME = os.getenv("CATALYST_SDK_APP_NAME", "ZohoAnalyticsRemoteMCPServer")
    CATALYST_PROJECT_ID = os.getenv("CATALYST_PROJECT_ID")
    CATALYST_ZAID = os.getenv("CATALYST_ZAID")
    CATALYST_ENVIRONMENT = os.getenv("CATALYST_ENVIRONMENT", "Production")
    CATALYST_CLIENT_ID = os.getenv("CATALYST_CLIENT_ID")
    CATALYST_CLIENT_SECRET = os.getenv("CATALYST_CLIENT_SECRET")
    CATALYST_REFRESH_TOKEN = os.getenv("CATALYST_REFRESH_TOKEN")
    CATALYST_CACHE_SEGMENT_ID = os.getenv("CATALYST_CACHE_SEGMENT_ID")
    CATALYST_PROJECT_DOMAIN = os.getenv("CATALYST_PROJECT_DOMAIN", "https://api.catalyst.zoho.in")


    CONSTANT_REMOTE_HOSTED_LOCATION = "REMOTE"
    CONSTANT_LOCAL_HOSTED_LOCATION = "LOCAL"


    OAUTH_DEFAULT_SCOPE = os.getenv("OAUTH_DEFAULT_SCOPE", "ZohoAnalytics.fullaccess.all")
    OAUTH_OFFLINE_ACCESS_SCOPE = os.getenv("OAUTH_OFFLINE_ACCESS_SCOPE", "offline_access")
    OAUTH_MAX_CLIENT_NAME_LENGTH = int(os.getenv("OAUTH_MAX_CLIENT_NAME_LENGTH", "80"))
    OAUTH_MAX_STRING_LENGTH = int(os.getenv("OAUTH_MAX_STRING_LENGTH", "256"))
    OAUTH_MAX_SCOPE_LENGTH = int(os.getenv("OAUTH_MAX_SCOPE_LENGTH", "100"))
    OAUTH_MAX_REDIRECT_URIS = int(os.getenv("OAUTH_MAX_REDIRECT_URIS", "5"))
    OAUTH_MAX_GRANT_TYPES = int(os.getenv("OAUTH_MAX_GRANT_TYPES", "2"))
    OAUTH_MAX_RESPONSE_TYPES = int(os.getenv("OAUTH_MAX_RESPONSE_TYPES", "1"))
    OAUTH_AUTH_TRANSACTION_TTL = int(os.getenv("OAUTH_AUTH_TRANSACTION_TTL", "120"))
    OAUTH_AUTH_CODE_TTL = int(os.getenv("OAUTH_AUTH_CODE_TTL", "120"))
    OAUTH_REGISTERED_CLIENTS_TTL = int(os.getenv("OAUTH_REGISTERED_CLIENTS_TTL", "36000"))
    OAUTH_CLIENT_IP_MAPPING_TTL = int(os.getenv("OAUTH_CLIENT_IP_MAPPING_TTL", "18000"))

    GLOBAL_OAUTH_RATE_LIMIT_CAPACITY = int(os.getenv("GLOBAL_OAUTH_RATE_LIMIT_CAPACITY", "30"))
    GLOBAL_OAUTH_RATE_LIMIT_WINDOW = int(os.getenv("GLOBAL_OAUTH_RATE_LIMIT_WINDOW", "60"))

    PRIVATE_OAUTH_STANDARD_RATE_LIMIT_COUNT = int(os.getenv("PRIVATE_OAUTH_STANDARD_RATE_LIMIT_COUNT", "5"))
    PRIVATE_OAUTH_STANDARD_RATE_LIMIT_WINDOW = int(os.getenv("PRIVATE_OAUTH_STANDARD_RATE_LIMIT_WINDOW", "60"))
    PUBLIC_OAUTH_STANDARD_RATE_LIMIT_COUNT = int(os.getenv("PUBLIC_OAUTH_STANDARD_RATE_LIMIT_COUNT", "100"))
    PUBLIC_OAUTH_STANDARD_RATE_LIMIT_WINDOW = int(os.getenv("PUBLIC_OAUTH_STANDARD_RATE_LIMIT_WINDOW", "60"))

    PRIVATE_OAUTH_REGISTRATION_RATE_LIMIT_COUNT = int(os.getenv("PRIVATE_OAUTH_REGISTRATION_RATE_LIMIT_COUNT", "10"))
    PRIVATE_OAUTH_REGISTRATION_RATE_LIMIT_WINDOW = int(os.getenv("PRIVATE_OAUTH_REGISTRATION_RATE_LIMIT_WINDOW", "3600"))
    PUBLIC_OAUTH_REGISTRATION_RATE_LIMIT_COUNT = int(os.getenv("PUBLIC_OAUTH_REGISTRATION_RATE_LIMIT_COUNT", "50"))
    PUBLIC_OAUTH_REGISTRATION_RATE_LIMIT_WINDOW = int(os.getenv("PUBLIC_OAUTH_REGISTRATION_RATE_LIMIT_WINDOW", "3600"))

    PRIVATE_OAUTH_MAX_CLIENTS_PER_IP = int(os.getenv("PRIVATE_OAUTH_MAX_CLIENTS_PER_IP", "5"))
    PUBLIC_OAUTH_MAX_CLIENTS_PER_IP = int(os.getenv("PUBLIC_OAUTH_MAX_CLIENTS_PER_IP", "0"))

    @classmethod
    def _is_public(cls) -> bool:
        if cls.DEPLOYMENT_SCENARIO not in ("private_network", "public_network"):
            raise ValueError(
                f"Invalid DEPLOYMENT_SCENARIO: {cls.DEPLOYMENT_SCENARIO}. "
                "Must be 'private_network' or 'public_network'."
            )
        return cls.DEPLOYMENT_SCENARIO == "public_network"

    @classmethod
    def get_standard_rate_limit(cls) -> tuple[int, int]:
        """Return (count, window_seconds) for standard endpoints."""
        if cls._is_public():
            return (
                cls.PUBLIC_OAUTH_STANDARD_RATE_LIMIT_COUNT,
                cls.PUBLIC_OAUTH_STANDARD_RATE_LIMIT_WINDOW,
            )
        return (
            cls.PRIVATE_OAUTH_STANDARD_RATE_LIMIT_COUNT,
            cls.PRIVATE_OAUTH_STANDARD_RATE_LIMIT_WINDOW,
        )

    @classmethod
    def get_registration_rate_limit(cls) -> tuple[int, int]:
        """Return (count, window_seconds) for client registration."""
        if cls._is_public():
            return (
                cls.PUBLIC_OAUTH_REGISTRATION_RATE_LIMIT_COUNT,
                cls.PUBLIC_OAUTH_REGISTRATION_RATE_LIMIT_WINDOW,
            )
        return (
            cls.PRIVATE_OAUTH_REGISTRATION_RATE_LIMIT_COUNT,
            cls.PRIVATE_OAUTH_REGISTRATION_RATE_LIMIT_WINDOW,
        )

    @classmethod
    def get_max_clients_per_ip(cls) -> int | None:
        """Return the max clients per IP, or None if the limit is disabled."""
        if cls._is_public():
            limit = cls.PUBLIC_OAUTH_MAX_CLIENTS_PER_IP
            return None if limit == 0 else limit
        return cls.PRIVATE_OAUTH_MAX_CLIENTS_PER_IP


    @staticmethod
    def get_allowed_org_ids():
        """Parse comma-separated org IDs into a list, filtering out empty values."""
        if not Settings.MCP_SERVER_ORG_IDS:
            return []
        return [org_id.strip() for org_id in Settings.MCP_SERVER_ORG_IDS.split(",") if org_id.strip()]

    @classmethod
    def _build_account(cls, key: str) -> ZohoAccount:
        suffix = f"_{key}"
        analytics_server_url = cls._normalize_server_url(
            os.getenv(f"ANALYTICS_SERVER_URL{suffix}"),
            cls.ANALYTICS_SERVER_URL,
        )
        accounts_server_url = cls._normalize_server_url(os.getenv(f"ACCOUNTS_SERVER_URL{suffix}"))
        if not accounts_server_url and analytics_server_url:
            accounts_server_url = cls._get_accounts_url(urlparse(analytics_server_url).netloc)

        return ZohoAccount(
            key=key,
            alias=(os.getenv(f"ANALYTICS_ACCOUNT_{key}_ALIAS") or f"account_{key}").strip().lower(),
            client_id=os.getenv(f"ANALYTICS_CLIENT_ID{suffix}") or (cls.CLIENT_ID if key == "1" else None),
            client_secret=os.getenv(f"ANALYTICS_CLIENT_SECRET{suffix}") or (cls.CLIENT_SECRET if key == "1" else None),
            refresh_token=os.getenv(f"ANALYTICS_REFRESH_TOKEN{suffix}") or (cls.REFRESH_TOKEN if key == "1" else None),
            org_id=os.getenv(f"ANALYTICS_ORG_ID{suffix}") or (cls.ORG_ID if key == "1" else "-1"),
            analytics_server_url=analytics_server_url or "https://analyticsapi.zoho.com",
            accounts_server_url=accounts_server_url,
        )

    @classmethod
    def get_accounts(cls) -> dict[str, ZohoAccount]:
        accounts = {"1": cls._build_account("1")}
        account_2 = cls._build_account("2")
        if account_2.client_id or account_2.client_secret or account_2.refresh_token:
            accounts["2"] = account_2
        return accounts

    @classmethod
    def get_account(cls, account: str | None = None) -> ZohoAccount:
        account_key = (account or _current_account.get() or os.getenv("ANALYTICS_DEFAULT_ACCOUNT") or "1").strip().lower()
        accounts = cls.get_accounts()
        for key, zoho_account in accounts.items():
            valid_names = {key, f"account_{key}", zoho_account.alias}
            if account_key in valid_names:
                missing = [
                    name for name, value in {
                        f"ANALYTICS_CLIENT_ID_{key}": zoho_account.client_id,
                        f"ANALYTICS_CLIENT_SECRET_{key}": zoho_account.client_secret,
                        f"ANALYTICS_REFRESH_TOKEN_{key}": zoho_account.refresh_token,
                    }.items()
                    if not value
                ]
                if missing:
                    raise RuntimeError(f"Missing environment variables for Zoho account {key}: {', '.join(missing)}")
                return zoho_account

        available = ", ".join(
            f"{key} ({zoho_account.alias})" for key, zoho_account in accounts.items()
        )
        raise ValueError(f"Unknown Zoho account '{account_key}'. Available accounts: {available}")

    @staticmethod
    def set_current_account(account: str | None):
        return _current_account.set(account)

    @staticmethod
    def reset_current_account(token):
        _current_account.reset(token)

    @classmethod
    def default_org_id(cls, account: str | None = None) -> str:
        if cls.HOSTED_LOCATION == cls.CONSTANT_REMOTE_HOSTED_LOCATION:
            return cls.ORG_ID
        return cls.get_account(account).org_id


@contextmanager
def use_zoho_account(account: str | None):
    if Settings.HOSTED_LOCATION == Settings.CONSTANT_REMOTE_HOSTED_LOCATION:
        yield None
        return
    token = Settings.set_current_account(account)
    try:
        yield Settings.get_account(account)
    finally:
        Settings.reset_current_account(token)


# Scenario-aware derived values kept for backward compatibility with existing imports
# Settings.OAUTH_STANDARD_RATE_LIMIT_COUNT, Settings.OAUTH_STANDARD_RATE_LIMIT_WINDOW = Settings.get_standard_rate_limit()
# Settings.OAUTH_REGISTRATION_RATE_LIMIT_COUNT, Settings.OAUTH_REGISTRATION_RATE_LIMIT_WINDOW = Settings.get_registration_rate_limit()
# Settings.OAUTH_MAX_CLIENTS_PER_IP = Settings.get_max_clients_per_ip()


def get_access_token():
    """
    For getting the access token from the MCP server.
    """
    request: Request = get_http_request()
    auth_header = request.headers.get("Authorization")
    access_token = auth_header.split(" ")[1]
    return access_token

analytics_clients: dict[str, AnalyticsClient] = {}
def get_analytics_client_instance(access_token = None) -> AnalyticsClient:
    """
    Returns a singleton instance of the AnalyticsClient.
    If access_token is provided, returns a new AnalyticsClient instance using that token.
    Otherwise, returns (or creates) the singleton client using credentials from Settings.
    """

    if Settings.HOSTED_LOCATION == Settings.CONSTANT_REMOTE_HOSTED_LOCATION:
        if access_token is None:
            access_token = get_access_token()
        client = AnalyticsClient.from_access_token(access_token)
        client.accounts_server_url = Settings.accounts_server_url()
        client.analytics_server_url = Settings.ANALYTICS_SERVER_URL
        return client


    account = Settings.get_account()
    if account.key not in analytics_clients:
        analytics_client = AnalyticsClient.from_refresh_token(account.client_id, account.client_secret, account.refresh_token)
        if account.accounts_server_url is None or account.analytics_server_url is None:
            raise RuntimeError("ACCOUNTS_SERVER_URL (or) ANALYTICS_SERVER_URL environment variable is not set. Please set it to your Zoho Analytics accounts server URL and analytics server URL respectively.")
        analytics_client.accounts_server_url = account.accounts_server_url
        analytics_client.analytics_server_url = account.analytics_server_url
        analytics_clients[account.key] = analytics_client
    return analytics_clients[account.key]
    
