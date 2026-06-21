import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import NotFoundException
from app.models.topic import Topic
from app.repositories.subject_repository import SubjectRepository
from app.repositories.topic_repository import TopicRepository

logger = logging.getLogger(__name__)


class TopicService:

    def __init__(self, topic_repository: TopicRepository, subject_repository: SubjectRepository):
        self.topic_repository = topic_repository
        self.subject_repository = subject_repository

    async def create_topic(
        self,
        subject_id: UUID,
        name: str,
        description: str | None = None,
        order: int = 0,
    ):

        db = self.topic_repository.db

        try:
            subject = await self.subject_repository.get_by_id(subject_id)

            if not subject:
                raise NotFoundException(f"Subject not found: {subject_id}")

            topic = Topic(
                subject_id=subject_id,
                name=name,
                description=description,
                order=order,
            )

            await self.topic_repository.create(topic)

            await db.commit()
            await db.refresh(topic)

            logger.info(f"Topic created: {name} for subject {subject_id}")

            return topic

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while creating topic: {name}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while creating topic: {name}")
            raise

    async def get_topic(self, topic_id: UUID):

        topic = await self.topic_repository.get_by_id(topic_id)

        if not topic:
            raise NotFoundException(f"Topic not found: {topic_id}")

        return topic

    async def get_topics_by_subject(self, subject_id: UUID, include_archived: bool = False):

        subject = await self.subject_repository.get_by_id(subject_id)

        if not subject:
            raise NotFoundException(f"Subject not found: {subject_id}")

        return await self.topic_repository.get_by_subject(subject_id, include_archived=include_archived)

    async def update_topic(self, topic_id: UUID, **kwargs):

        db = self.topic_repository.db

        try:
            topic = await self.get_topic(topic_id)

            for key, value in kwargs.items():
                if value is not None:
                    setattr(topic, key, value)

            await self.topic_repository.update(topic)

            await db.commit()
            await db.refresh(topic)

            logger.info(f"Topic updated: {topic_id}")

            return topic

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while updating topic: {topic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while updating topic: {topic_id}")
            raise

    async def reorder_topics(self, subject_id: UUID, ordered_ids: list[UUID]):

        db = self.topic_repository.db

        try:
            topics = await self.topic_repository.get_by_subject(subject_id)
            topic_map = {t.id: t for t in topics}

            for index, topic_id in enumerate(ordered_ids):
                topic = topic_map.get(topic_id)
                if topic:
                    topic.order = index + 1
                    await self.topic_repository.update(topic)

            await db.commit()

            logger.info(f"Topics reordered for subject {subject_id}")

            return await self.topic_repository.get_by_subject(subject_id)

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while reordering topics for subject: {subject_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while reordering topics for subject: {subject_id}")
            raise

    async def delete_topic(self, topic_id: UUID):

        db = self.topic_repository.db

        try:
            topic = await self.get_topic(topic_id)

            await self.topic_repository.delete(topic)

            await db.commit()

            logger.info(f"Topic deleted: {topic_id}")

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while deleting topic: {topic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while deleting topic: {topic_id}")
            raise

    async def archive_topic(self, topic_id: UUID, archive: bool = True):
        db = self.topic_repository.db
        try:
            topic = await self.get_topic(topic_id)
            topic.is_archived = archive
            await self.topic_repository.update(topic)
            await db.commit()
            await db.refresh(topic)
            action = "archived" if archive else "unarchived"
            logger.info(f"Topic {action}: {topic_id}")
            return topic
        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while archiving topic: {topic_id}")
            raise
        except Exception:
            await db.rollback()
            logger.exception(f"Error while archiving topic: {topic_id}")
            raise
