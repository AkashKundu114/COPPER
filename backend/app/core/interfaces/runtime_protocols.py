"""Abstract Provider Interfaces and Protocols for C.O.P.P.E.R.

Establishes formal typing Protocols for model runtimes, storage adapters,
and tool handlers to ensure loose coupling, high testability, and swappable providers.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ModelRuntimeProtocol(Protocol):
    """Protocol for local or remote LLM runtime engines."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Executes a chat completion."""
        ...

    async def generate_embeddings(
        self,
        text: str,
        model: str = "nomic-embed-text",
    ) -> list[float]:
        """Generates dense vector embeddings for input text."""
        ...

    async def unload_model(self, model_name: str) -> bool:
        """Requests explicit memory/VRAM offloading of model weights."""
        ...


@runtime_checkable
class StorageAdapterProtocol(Protocol):
    """Protocol for pluggable persistence storage engines."""

    async def get(self, key: str) -> Any | None:
        """Retrieves a record by unique key."""
        ...

    async def put(self, key: str, value: Any, ttl_seconds: int | None = None) -> bool:
        """Stores or updates a record with optional expiration."""
        ...

    async def delete(self, key: str) -> bool:
        """Deletes a record by key."""
        ...

    async def exists(self, key: str) -> bool:
        """Checks existence of key."""
        ...


@runtime_checkable
class SearchProviderProtocol(Protocol):
    """Protocol for pluggable web and epistemic search engines."""

    async def search(
        self,
        query: str,
        limit: int = 5,
        categories: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Executes search query returning ranked list of result dicts."""
        ...
