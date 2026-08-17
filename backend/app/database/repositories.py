from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .connection import mongodb


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisRepository:

    @property
    def collection(self):
        if mongodb.database is None:
            return None

        return mongodb.database.analyses

    async def create(self, document: dict[str, Any]) -> bool:
        collection = self.collection

        if collection is None:
            return False

        await collection.insert_one(document)
        return True

    async def get_history(
        self,
        user_id: str = "anonymous",
        limit: int = 20,
    ) -> list[dict[str, Any]]:

        collection = self.collection

        if collection is None:
            return []

        cursor = (
            collection
            .find(
                {"user_id": user_id},
                {
                    "_id": 0,
                    "analysis_id": 1,
                    "headline": 1,
                    "final_decision": 1,
                    "final_confidence": 1,
                    "created_at": 1,
                },
            )
            .sort("created_at", -1)
            .limit(limit)
        )

        return await cursor.to_list(length=limit)

    async def get_by_id(
        self,
        analysis_id: str,
    ) -> Optional[dict[str, Any]]:

        collection = self.collection

        if collection is None:
            return None

        return await collection.find_one(
            {"analysis_id": analysis_id},
            {"_id": 0},
        )

    async def delete(
        self,
        analysis_id: str,
    ) -> bool:

        collection = self.collection

        if collection is None:
            return False

        result = await collection.delete_one(
            {"analysis_id": analysis_id}
        )

        return result.deleted_count > 0


class ClaimRepository:

    @property
    def collection(self):
        if mongodb.database is None:
            return None

        return mongodb.database.claims

    async def create_many(
        self,
        claims: list[dict[str, Any]],
    ) -> bool:

        collection = self.collection

        if collection is None or not claims:
            return False

        await collection.insert_many(claims)
        return True

    async def get_by_analysis(
        self,
        analysis_id: str,
    ) -> list[dict[str, Any]]:

        collection = self.collection

        if collection is None:
            return []

        cursor = collection.find(
            {
                "analysis_id": analysis_id
            },
            {
                "_id": 0
            },
        )

        return await cursor.to_list(length=None)

    async def delete_by_analysis(
        self,
        analysis_id: str,
    ) -> None:

        collection = self.collection

        if collection is not None:
            await collection.delete_many(
                {"analysis_id": analysis_id}
            )


class EvidenceRepository:

    @property
    def collection(self):
        if mongodb.database is None:
            return None

        return mongodb.database.evidence

    async def create_many(
        self,
        evidence: list[dict[str, Any]],
    ) -> bool:

        collection = self.collection

        if collection is None or not evidence:
            return False

        await collection.insert_many(evidence)
        return True

    async def get_by_analysis(
        self,
        analysis_id: str,
    ) -> list[dict[str, Any]]:

        collection = self.collection

        if collection is None:
            return []

        cursor = collection.find(
            {
                "analysis_id": analysis_id
            },
            {
                "_id": 0
            },
        )

        return await cursor.to_list(length=None)

    async def delete_by_analysis(
        self,
        analysis_id: str,
    ) -> None:

        collection = self.collection

        if collection is not None:
            await collection.delete_many(
                {"analysis_id": analysis_id}
            )


analysis_repository = AnalysisRepository()
claim_repository = ClaimRepository()
evidence_repository = EvidenceRepository()
class FeedbackRepository:
    """Repository for user feedback on completed analyses."""

    @property
    def collection(self):
        if mongodb.database is None:
            return None

        return mongodb.database.feedback

    async def create(
        self,
        document: dict[str, Any],
    ) -> bool:
        """Store feedback."""

        collection = self.collection

        if collection is None:
            return False

        await collection.insert_one(document)
        return True

    async def get_by_analysis(
        self,
        analysis_id: str,
    ) -> list[dict[str, Any]]:
        """Return feedback associated with an analysis."""

        collection = self.collection

        if collection is None:
            return []

        cursor = collection.find(
            {"analysis_id": analysis_id},
            {"_id": 0},
        )

        return await cursor.to_list(length=None)


feedback_repository = FeedbackRepository()