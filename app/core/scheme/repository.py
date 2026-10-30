"""Database repositories for scheme catalog and immutable versioned rules.

Conforms to Directive M4.5, 07_SCHEME_ENGINE_AND_GOVERNANCE.md, and 10_DATA_MODEL.md.
"""

import hashlib
import json
from typing import List, Optional, Sequence
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.scheme import Scheme, SchemeRuleVersion


class SchemeCatalogRepository:
    """Access layer for validated scheme catalog entries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_scheme_id(self, scheme_id: str) -> Optional[Scheme]:
        """Fetch scheme by unique string scheme_id with its latest rule versions."""
        stmt = (
            select(Scheme)
            .where(Scheme.scheme_id == scheme_id)
            .options(selectinload(Scheme.rule_versions))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_active(
        self,
        classification: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Sequence[Scheme]:
        """List active schemes filtered optionally by classification or assistance category."""
        stmt = (
            select(Scheme)
            .where(Scheme.active.is_(True))
            .options(selectinload(Scheme.rule_versions))
        )
        if classification:
            stmt = stmt.where(Scheme.classification == classification)
        if category:
            stmt = stmt.where(Scheme.assistance_category == category)
        res = await self.db.execute(stmt)
        return res.scalars().all()


class SchemeRuleRepository:
    """Access layer for immutable, cryptographic-hashed rule versions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_version(self, scheme_id: str) -> Optional[SchemeRuleVersion]:
        """Fetch the latest active rule version for a scheme."""
        stmt = (
            select(SchemeRuleVersion)
            .join(Scheme, Scheme.id == SchemeRuleVersion.scheme_id)
            .where(Scheme.scheme_id == scheme_id)
            .order_by(SchemeRuleVersion.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_specific_version(
        self, scheme_id: str, rule_version: str
    ) -> Optional[SchemeRuleVersion]:
        """Fetch an immutable historical rule version for replay or audit."""
        stmt = (
            select(SchemeRuleVersion)
            .join(Scheme, Scheme.id == SchemeRuleVersion.scheme_id)
            .where(
                Scheme.scheme_id == scheme_id,
                SchemeRuleVersion.rule_version == rule_version,
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    def compute_definition_hash(definition: dict) -> str:
        """Compute deterministic SHA-256 hash of rule definition dictionary."""
        def_str = json.dumps(definition, sort_keys=True)
        return hashlib.sha256(def_str.encode("utf-8")).hexdigest()
