import logging
import os
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import NotFoundException
from app.models.subtopic import SubTopic
from app.models.subtopic_file import SubtopicFile
from app.repositories.subtopic_repository import SubTopicRepository
from app.repositories.subtopic_file_repository import SubtopicFileRepository
from app.repositories.topic_repository import TopicRepository

logger = logging.getLogger(__name__)


class SubTopicService:

    def __init__(
        self,
        subtopic_repository: SubTopicRepository,
        topic_repository: TopicRepository,
        file_repository: SubtopicFileRepository,
    ):
        self.subtopic_repository = subtopic_repository
        self.topic_repository = topic_repository
        self.file_repository = file_repository

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
        questions_correct: int,
        mistake_count: int,
    ):

        db = self.subtopic_repository.db

        try:
            subtopic = await self.get_subtopic(subtopic_id)

            subtopic.questions_correct = questions_correct
            subtopic.mistake_count = mistake_count
            subtopic.questions_solved = questions_correct + mistake_count

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

    # ── Notes ──

    async def save_notes(
        self,
        subtopic_id: UUID,
        notes_html: str | None = None,
        sketch_data_url: str | None = None,
        whiteboard_data_url: str | None = None,
    ):
        db = self.subtopic_repository.db

        try:
            subtopic = await self.get_subtopic(subtopic_id)

            if notes_html is not None:
                subtopic.notes_html = notes_html
            if sketch_data_url is not None:
                subtopic.sketch_data_url = sketch_data_url
            if whiteboard_data_url is not None:
                subtopic.whiteboard_data_url = whiteboard_data_url

            await self.subtopic_repository.update(subtopic)

            await db.commit()
            await db.refresh(subtopic)

            logger.info(f"Notes saved for subtopic: {subtopic_id}")

            return subtopic

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while saving notes: {subtopic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while saving notes: {subtopic_id}")
            raise

    # ── Files ──

    async def create_file(
        self,
        subtopic_id: UUID,
        original_name: str,
        content_type: str,
        size: int,
        storage_path: str,
        disk_name: str,
    ):
        db = self.file_repository.db

        try:
            # Validate subtopic exists
            await self.get_subtopic(subtopic_id)

            file_record = SubtopicFile(
                subtopic_id=subtopic_id,
                name=disk_name,
                original_name=original_name,
                content_type=content_type,
                size=size,
                storage_path=storage_path,
            )

            await self.file_repository.create(file_record)

            await db.commit()
            await db.refresh(file_record)

            logger.info(f"File record created: {original_name} for subtopic {subtopic_id}")

            return file_record

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while creating file record: {original_name}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while creating file record: {original_name}")
            raise

    async def get_files(self, subtopic_id: UUID):
        return await self.file_repository.get_by_subtopic(subtopic_id)

    async def get_file(self, file_id: UUID):
        file_record = await self.file_repository.get_by_id(file_id)
        if not file_record:
            raise NotFoundException(f"File not found: {file_id}")
        return file_record

    async def delete_file(self, file_id: UUID):
        db = self.file_repository.db

        try:
            file_record = await self.get_file(file_id)

            # Delete from disk
            if os.path.exists(file_record.storage_path):
                os.remove(file_record.storage_path)
                logger.info(f"File deleted from disk: {file_record.storage_path}")

            await self.file_repository.delete(file_record)

            await db.commit()

            logger.info(f"File record deleted: {file_id}")

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while deleting file: {file_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while deleting file: {file_id}")
            raise
