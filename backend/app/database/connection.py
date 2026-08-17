from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError


class MongoDB:
    """
    Async MongoDB connection manager.

    The application can continue running when MongoDB is unavailable.
    """

    def __init__(self) -> None:
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.connected: bool = False

    async def connect(self, uri: str, database_name: str) -> bool:
        """
        Connect to MongoDB and verify the connection with ping.
        """
        try:
            self.client = AsyncIOMotorClient(
                uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
            )

            await self.client.admin.command("ping")

            self.database = self.client[database_name]
            self.connected = True

            await self.create_indexes()

            return True

        except PyMongoError:
            self.connected = False
            self.database = None

            if self.client:
                self.client.close()

            self.client = None
            return False

    async def disconnect(self) -> None:
        """
        Close MongoDB connection.
        """
        if self.client:
            self.client.close()

        self.client = None
        self.database = None
        self.connected = False

    async def create_indexes(self) -> None:
        """
        Create indexes required by the application.
        """
        if self.database is None:
            return

        await self.database.analyses.create_index(
            [("user_id", 1)]
        )

        await self.database.analyses.create_index(
            [("created_at", -1)]
        )

        await self.database.analyses.create_index(
            [("final_decision", 1)]
        )

        await self.database.claims.create_index(
            [("analysis_id", 1)]
        )

        await self.database.evidence.create_index(
            [("analysis_id", 1)]
        )

        await self.database.evidence.create_index(
            [("claim_id", 1)]
        )

        await self.database.feedback.create_index(
            [("analysis_id", 1)]
        )

        await self.database.feedback.create_index(
            [("user_id", 1)]
        )


# Application-wide MongoDB manager
mongodb = MongoDB()