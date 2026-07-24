"""
App-level configuration model for HealthChain projects.

Loads and validates healthchain.yaml from the project root.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

_CONFIG_FILENAME = "healthchain.yaml"


class SourceConfig(BaseModel):
    """A FHIR data source. Credentials are loaded from environment variables."""

    env_prefix: str  # e.g. "MEDPLUM" reads MEDPLUM_CLIENT_ID, MEDPLUM_BASE_URL etc.

    def to_fhir_auth_config(self):
        """Instantiate FHIRAuthConfig by reading env vars for this source's prefix."""
        from healthchain.gateway.clients.fhir.base import FHIRAuthConfig

        return FHIRAuthConfig.from_env(self.env_prefix)


class LLMConfig(BaseModel):
    """LLM provider settings. API key is read from the standard env var for each provider."""

    provider: str = "anthropic"  # anthropic | openai | google | huggingface
    model: str = "claude-opus-4-8"
    max_tokens: int = 512

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = {"anthropic", "openai", "google", "huggingface"}
        if v not in allowed:
            raise ValueError(f"provider must be one of: {', '.join(sorted(allowed))}")
        return v


class ServiceConfig(BaseModel):
    type: str = "fhir-gateway"
    port: int = 8000


class TLSConfig(BaseModel):
    enabled: bool = False
    cert_path: str = "./certs/server.crt"
    key_path: str = "./certs/server.key"


class SecurityConfig(BaseModel):
    auth: str = "none"
    tls: TLSConfig = TLSConfig()
    allowed_origins: List[str] = ["*"]

    @field_validator("auth")
    @classmethod
    def validate_auth(cls, v: str) -> str:
        allowed = {"none", "api-key"}
        if v not in allowed:
            raise ValueError(f"auth must be one of: {', '.join(sorted(allowed))}")
        return v


class ComplianceConfig(BaseModel):
    audit_log: Optional[str] = None


class GovernanceConfig(BaseModel):
    """Declarative governance context for a deployment."""

    standards: List[str] = []
    clinical_safety_officer: str = ""
    data_access_agreement: str = ""
    dpia_required: bool = False
    notes: str = ""


class SiteConfig(BaseModel):
    name: str = ""
    environment: str = "development"

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(
                f"environment must be one of: {', '.join(sorted(allowed))}"
            )
        return v


class AppConfig(BaseModel):
    name: str = "my-healthchain-app"
    version: str = "1.0.0"
    service: ServiceConfig = ServiceConfig()
    security: SecurityConfig = SecurityConfig()
    compliance: ComplianceConfig = ComplianceConfig()
    governance: GovernanceConfig = GovernanceConfig()
    site: SiteConfig = SiteConfig()
    sources: Dict[str, SourceConfig] = {}
    llm: Optional[LLMConfig] = None

    @classmethod
    def from_yaml(cls, path: Path) -> "AppConfig":
        """Load AppConfig from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    @classmethod
    def load(cls) -> Optional["AppConfig"]:
        """Load healthchain.yaml from the current working directory if it exists.

        Also loads .env into the environment before parsing config, so credentials
        are available to any component initialised from the returned config object.
        """
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

        config_path = Path(_CONFIG_FILENAME)
        if config_path.exists():
            try:
                return cls.from_yaml(config_path)
            except Exception as e:
                logger.warning(f"Failed to load {_CONFIG_FILENAME}: {e}")
        return None
