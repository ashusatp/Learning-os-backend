import logging
import os
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import BadRequestException, NotFoundException
from app.models.subtopic import SubTopic
from app.models.subtopic_file import SubtopicFile
from app.models.subtopic_folder import SubtopicFolder
from app.models.question import Question
from app.models.mistake import Mistake
from app.repositories.subtopic_repository import SubTopicRepository
from app.repositories.subtopic_file_repository import SubtopicFileRepository
from app.repositories.subtopic_folder_repository import SubtopicFolderRepository
from app.repositories.topic_repository import TopicRepository

logger = logging.getLogger(__name__)


class SubTopicService:

    def __init__(
        self,
        subtopic_repository: SubTopicRepository,
        topic_repository: TopicRepository,
        file_repository: SubtopicFileRepository,
        folder_repository: SubtopicFolderRepository | None = None,
    ):
        self.subtopic_repository = subtopic_repository
        self.topic_repository = topic_repository
        self.file_repository = file_repository
        self.folder_repository = folder_repository

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
            await db.refresh(subtopic, ["files"])

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
            await db.refresh(subtopic, ["files"])

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
            await db.refresh(subtopic, ["files"])

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

    async def record_revision_stats(self, subtopic_id: UUID):
        """Record revision and return stats."""
        await self.record_revision(subtopic_id)
        return await self.get_stats(subtopic_id)

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
            await db.refresh(subtopic, ["files"])

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

    # ── Stats ──

    async def get_stats(self, subtopic_id: UUID):
        subtopic = await self.get_subtopic(subtopic_id)
        db = self.subtopic_repository.db

        # Question count
        q_count = await db.execute(
            select(func.count()).select_from(Question).where(Question.subtopic_id == subtopic_id)
        )
        question_count = q_count.scalar()

        # Mistake counts
        total_q = await db.execute(
            select(func.count()).select_from(Mistake).where(Mistake.subtopic_id == subtopic_id)
        )
        total_mistakes = total_q.scalar()

        resolved_q = await db.execute(
            select(func.count()).select_from(Mistake).where(
                Mistake.subtopic_id == subtopic_id,
                Mistake.is_resolved == True,
            )
        )
        resolved_mistakes = resolved_q.scalar()

        return {
            "mastery_level": subtopic.mastery_level,
            "confidence_level": subtopic.confidence_level,
            "revision_count": subtopic.revision_count,
            "last_revised_at": subtopic.last_revised_at,
            "question_count": question_count,
            "total_mistakes": total_mistakes,
            "unresolved_mistakes": total_mistakes - resolved_mistakes,
            "resolved_mistakes": resolved_mistakes,
            "created_at": subtopic.created_at,
            "updated_at": subtopic.updated_at,
        }

    async def update_stats(self, subtopic_id: UUID, **kwargs):
        db = self.subtopic_repository.db

        try:
            subtopic = await self.get_subtopic(subtopic_id)

            for key, value in kwargs.items():
                if value is not None:
                    setattr(subtopic, key, value)

            await self.subtopic_repository.update(subtopic)
            await db.commit()
            await db.refresh(subtopic, ["files"])

            logger.info(f"Stats updated for subtopic: {subtopic_id}")
            return await self.get_stats(subtopic_id)

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while updating stats: {subtopic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while updating stats: {subtopic_id}")
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
            await db.refresh(subtopic, ["files"])

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
        folder_id: UUID | None = None,
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
                folder_id=folder_id,
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

    async def get_files(self, subtopic_id: UUID, folder_id=None, filter_folder: bool = False):
        if filter_folder:
            return await self.file_repository.get_by_subtopic(subtopic_id, folder_id=folder_id)
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

    async def move_file(self, file_id: UUID, folder_id: UUID | None):
        db = self.file_repository.db

        try:
            file_record = await self.get_file(file_id)

            if folder_id is not None:
                folder = await self.folder_repository.get_by_id(folder_id)
                if not folder:
                    raise NotFoundException(f"Folder not found: {folder_id}")

            file_record.folder_id = folder_id
            await self.file_repository.update(file_record)
            await db.commit()
            await db.refresh(file_record)

            logger.info(f"File {file_id} moved to folder {folder_id}")
            return file_record

        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while moving file: {file_id}")
            raise

    async def rename_file(self, file_id: UUID, original_name: str):
        db = self.file_repository.db

        try:
            file_record = await self.get_file(file_id)
            file_record.original_name = original_name
            await self.file_repository.update(file_record)
            await db.commit()
            await db.refresh(file_record)

            logger.info(f"File {file_id} renamed to {original_name}")
            return file_record

        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while renaming file: {file_id}")
            raise

    # ── Folders ──

    async def create_folder(
        self,
        subtopic_id: UUID,
        name: str,
        parent_id: UUID | None = None,
    ):
        db = self.folder_repository.db

        try:
            await self.get_subtopic(subtopic_id)

            if parent_id is not None:
                parent = await self.folder_repository.get_by_id(parent_id)
                if not parent:
                    raise NotFoundException(f"Parent folder not found: {parent_id}")

            folder = SubtopicFolder(
                subtopic_id=subtopic_id,
                parent_id=parent_id,
                name=name,
            )
            await self.folder_repository.create(folder)
            await db.commit()
            await db.refresh(folder)

            logger.info(f"Folder created: {name} for subtopic {subtopic_id}")
            return folder

        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while creating folder: {name}")
            raise

    async def get_folder(self, folder_id: UUID):
        folder = await self.folder_repository.get_by_id(folder_id)
        if not folder:
            raise NotFoundException(f"Folder not found: {folder_id}")
        return folder

    async def get_folder_contents(self, subtopic_id: UUID, folder_id: UUID | None = None):
        folders = await self.folder_repository.get_by_subtopic(subtopic_id, parent_id=folder_id)
        files = await self.file_repository.get_by_subtopic(subtopic_id, folder_id=folder_id)
        return {"folders": folders, "files": files}

    async def rename_folder(self, folder_id: UUID, name: str):
        db = self.folder_repository.db

        try:
            folder = await self.get_folder(folder_id)
            folder.name = name
            await self.folder_repository.update(folder)
            await db.commit()
            await db.refresh(folder)

            logger.info(f"Folder {folder_id} renamed to {name}")
            return folder

        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while renaming folder: {folder_id}")
            raise

    async def move_folder(self, folder_id: UUID, parent_id: UUID | None):
        db = self.folder_repository.db

        try:
            folder = await self.get_folder(folder_id)

            if parent_id is not None:
                if parent_id == folder_id:
                    raise BadRequestException("Cannot move folder into itself")
                parent = await self.folder_repository.get_by_id(parent_id)
                if not parent:
                    raise NotFoundException(f"Parent folder not found: {parent_id}")

            folder.parent_id = parent_id
            await self.folder_repository.update(folder)
            await db.commit()
            await db.refresh(folder)

            logger.info(f"Folder {folder_id} moved to parent {parent_id}")
            return folder

        except (NotFoundException, BadRequestException):
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while moving folder: {folder_id}")
            raise

    async def delete_folder(self, folder_id: UUID):
        db = self.folder_repository.db

        try:
            folder = await self.get_folder(folder_id)
            await self.folder_repository.delete(folder)
            await db.commit()

            logger.info(f"Folder deleted: {folder_id}")

        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while deleting folder: {folder_id}")
            raise
