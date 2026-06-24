import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import NotFoundException
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.repositories.question_repository import QuestionRepository
from app.repositories.subtopic_repository import SubTopicRepository

logger = logging.getLogger(__name__)


class QuestionService:

    def __init__(
        self,
        question_repository: QuestionRepository,
        subtopic_repository: SubTopicRepository,
    ):
        self.question_repository = question_repository
        self.subtopic_repository = subtopic_repository

    async def create_question(self, subtopic_id: UUID, **kwargs):
        db = self.question_repository.db

        try:
            subtopic = await self.subtopic_repository.get_by_id(subtopic_id)
            if not subtopic:
                raise NotFoundException(f"Subtopic not found: {subtopic_id}")

            options_data = kwargs.pop("options", [])

            question = Question(subtopic_id=subtopic_id, **kwargs)

            for i, opt in enumerate(options_data):
                question.options.append(
                    QuestionOption(
                        text_html=opt["text_html"],
                        is_correct=opt.get("is_correct", False),
                        order=opt.get("order", i),
                    )
                )

            await self.question_repository.create(question)
            await db.commit()

            # Re-fetch with options eagerly loaded to avoid lazy-load outside async context
            question = await self.question_repository.get_by_id(question.id)

            logger.info(f"Question created for subtopic {subtopic_id}")
            return question

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while creating question for subtopic: {subtopic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while creating question for subtopic: {subtopic_id}")
            raise

    async def get_question(self, question_id: UUID):
        question = await self.question_repository.get_by_id(question_id)
        if not question:
            raise NotFoundException(f"Question not found: {question_id}")
        return question

    async def get_questions_by_subtopic(self, subtopic_id: UUID):
        subtopic = await self.subtopic_repository.get_by_id(subtopic_id)
        if not subtopic:
            raise NotFoundException(f"Subtopic not found: {subtopic_id}")
        return await self.question_repository.get_by_subtopic(subtopic_id)

    async def get_questions_by_subtopic_paginated(self, subtopic_id: UUID, page: int, page_size: int):
        subtopic = await self.subtopic_repository.get_by_id(subtopic_id)
        if not subtopic:
            raise NotFoundException(f"Subtopic not found: {subtopic_id}")
        offset = (page - 1) * page_size
        items, total = await self.question_repository.get_by_subtopic_paginated(subtopic_id, page_size, offset)
        total_pages = (total + page_size - 1) // page_size
        return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}

    async def get_questions_by_goal_paginated(self, goal_id: UUID, page: int, page_size: int, **filters):
        offset = (page - 1) * page_size
        rows, total = await self.question_repository.get_by_goal_paginated(
            goal_id, page_size, offset, **filters
        )
        total_pages = (total + page_size - 1) // page_size

        items = []
        for row in rows:
            question = row[0]
            item = {
                "id": question.id,
                "subtopic_id": question.subtopic_id,
                "question_type": question.question_type,
                "text_html": question.text_html,
                "explanation_html": question.explanation_html,
                "difficulty": question.difficulty,
                "marks": question.marks,
                "negative_marks": question.negative_marks,
                "numerical_answer": question.numerical_answer,
                "numerical_tolerance": question.numerical_tolerance,
                "answer_html": question.answer_html,
                "is_pyq": question.is_pyq,
                "tags": question.tags or [],
                "order": question.order,
                "options": question.options,
                "created_at": question.created_at,
                "updated_at": question.updated_at,
                "subject_id": row[1],
                "subject_name": row[2],
                "topic_id": row[3],
                "topic_name": row[4],
                "subtopic_name": row[5],
            }
            items.append(item)

        return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}

    async def update_question(self, question_id: UUID, **kwargs):
        db = self.question_repository.db

        try:
            question = await self.get_question(question_id)

            options_data = kwargs.pop("options", None)

            for key, value in kwargs.items():
                if value is not None:
                    setattr(question, key, value)

            # Sync options if provided
            if options_data is not None:
                await self._sync_options(question, options_data)

            await self.question_repository.update(question)
            await db.commit()

            question = await self.question_repository.get_by_id(question.id)

            logger.info(f"Question updated: {question_id}")
            return question

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while updating question: {question_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while updating question: {question_id}")
            raise

    async def _sync_options(self, question: Question, options_data: list[dict]):
        """Replace all options with the new set."""
        existing_map = {opt.id: opt for opt in question.options}
        incoming_ids = set()

        new_options = []
        for i, opt_data in enumerate(options_data):
            opt_id = opt_data.get("id")
            if opt_id and opt_id in existing_map:
                # Update existing
                existing = existing_map[opt_id]
                existing.text_html = opt_data["text_html"]
                existing.is_correct = opt_data.get("is_correct", False)
                existing.order = opt_data.get("order", i)
                incoming_ids.add(opt_id)
                new_options.append(existing)
            else:
                # Create new
                new_options.append(
                    QuestionOption(
                        text_html=opt_data["text_html"],
                        is_correct=opt_data.get("is_correct", False),
                        order=opt_data.get("order", i),
                    )
                )

        # Remove options not in the incoming set
        question.options = new_options

    async def delete_question(self, question_id: UUID):
        db = self.question_repository.db

        try:
            question = await self.get_question(question_id)
            await self.question_repository.delete(question)
            await db.commit()

            logger.info(f"Question deleted: {question_id}")

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while deleting question: {question_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while deleting question: {question_id}")
            raise

    async def reorder_questions(self, subtopic_id: UUID, ordered_ids: list[UUID]):
        db = self.question_repository.db

        try:
            questions = await self.question_repository.get_by_subtopic(subtopic_id)
            question_map = {q.id: q for q in questions}

            for index, qid in enumerate(ordered_ids):
                question = question_map.get(qid)
                if question:
                    question.order = index + 1
                    await self.question_repository.update(question)

            await db.commit()

            logger.info(f"Questions reordered for subtopic {subtopic_id}")
            return await self.question_repository.get_by_subtopic(subtopic_id)

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while reordering questions for subtopic: {subtopic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while reordering questions for subtopic: {subtopic_id}")
            raise
