import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import NotFoundException
from app.models.subtopic import SubTopic
from app.repositories.subtopic_repository import SubTopicRepository
from app.repositories.topic_repository import TopicRepository

logger = logging.getLogger(__name__)


class SubTopicService:

    def __init__(self, subtopic_repository: SubTopicRepository, topic_repository: TopicRepository):
        self.subtopic_repository = subtopic_repository
        self.topic_repository = topic_repository

    async def create_subtopic(
        self,
        topic_id: UUID,
        name: str,
        description: str | None = None,
        order: int = 0,
    ):

        db = self.subtopic_repository.db

        try:
            topic = await self.topic_repository.get_by_id(topic_id)

            if not topic:
                raise NotFoundException(f"Topic not found: {topic_id}")

            subtopic = SubTopic(
                topic_id=topic_id,
                name=name,
                description=description,
                order=order,
            )

            await self.subtopic_repository.create(subtopic)

            await db.commit()
            await db.refresh(subtopic)

            logger.info(f"SubTopic created: {name} for topic {topic_id}")

            return subtopic

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while creating subtopic: {name}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while creating subtopic: {name}")
            raise

    async def get_subtopic(self, subtopic_id: UUID):

        subtopic = await self.subtopic_repository.get_by_id(subtopic_id)

        if not subtopic:
            raise NotFoundException(f"SubTopic not found: {subtopic_id}")

        return subtopic

    async def get_subtopics_by_topic(self, topic_id: UUID):

        topic = await self.topic_repository.get_by_id(topic_id)

        if not topic:
            raise NotFoundException(f"Topic not found: {topic_id}")

        return await self.subtopic_repository.get_by_topic(topic_id)

    async def update_subtopic(self, subtopic_id: UUID, **kwargs):

        db = self.subtopic_repository.db

        try:
            subtopic = await self.get_subtopic(subtopic_id)

            for key, value in kwargs.items():
                if value is not None:
                    setattr(subtopic, key, value)

            await self.subtopic_repository.update(subtopic)

            await db.commit()
            await db.refresh(subtopic)

            logger.info(f"SubTopic updated: {subtopic_id}")

            return subtopic

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while updating subtopic: {subtopic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while updating subtopic: {subtopic_id}")
            raise

    async def reorder_subtopics(self, topic_id: UUID, ordered_ids: list[UUID]):

        db = self.subtopic_repository.db

        try:
            subtopics = await self.subtopic_repository.get_by_topic(topic_id)
            subtopic_map = {st.id: st for st in subtopics}

            for index, subtopic_id in enumerate(ordered_ids):
                subtopic = subtopic_map.get(subtopic_id)
                if subtopic:
                    subtopic.order = index + 1
                    await self.subtopic_repository.update(subtopic)

            await db.commit()

            logger.info(f"Subtopics reordered for topic {topic_id}")

            return await self.subtopic_repository.get_by_topic(topic_id)

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while reordering subtopics for topic: {topic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while reordering subtopics for topic: {topic_id}")
            raise

    async def delete_subtopic(self, subtopic_id: UUID):

        db = self.subtopic_repository.db

        try:
            subtopic = await self.get_subtopic(subtopic_id)

            await self.subtopic_repository.delete(subtopic)

            await db.commit()

            logger.info(f"SubTopic deleted: {subtopic_id}")

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while deleting subtopic: {subtopic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while deleting subtopic: {subtopic_id}")
            raise

    async def record_revision(self, subtopic_id: UUID):

        db = self.subtopic_repository.db

        try:
            subtopic = await self.get_subtopic(subtopic_id)

            subtopic.revision_count += 1
            subtopic.last_revised_at = datetime.now(timezone.utc)

            await self.subtopic_repository.update(subtopic)

            await db.commit()
            await db.refresh(subtopic)

            logger.info(f"Revision recorded for subtopic: {subtopic_id}")

            return subtopic

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while recording revision: {subtopic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while recording revision: {subtopic_id}")
            raise

    async def update_performance(
        self,
        subtopic_id: UUID,
        questions_solved: int,
        questions_correct: int,
        mistake_count: int,
    ):

        db = self.subtopic_repository.db

        try:
            subtopic = await self.get_subtopic(subtopic_id)

            subtopic.questions_solved = questions_solved
            subtopic.questions_correct = questions_correct
            subtopic.mistake_count = mistake_count

            await self.subtopic_repository.update(subtopic)

            await db.commit()
            await db.refresh(subtopic)

            logger.info(f"Performance updated for subtopic: {subtopic_id}")

            return subtopic

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while updating performance: {subtopic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while updating performance: {subtopic_id}")
            raise
