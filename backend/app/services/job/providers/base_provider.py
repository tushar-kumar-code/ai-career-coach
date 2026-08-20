from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class BaseJobProvider(ABC):
    """Abstract base class for job search providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider unique name identifier."""
        pass

    @abstractmethod
    async def search_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        remote_only: Optional[bool] = None,
        experience_level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search jobs from provider. Returns normalized job dictionaries."""
        pass

    @abstractmethod
    async def get_job_details(self, provider_job_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full job details by provider job ID."""
        pass
