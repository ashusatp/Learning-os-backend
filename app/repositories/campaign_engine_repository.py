import logging
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mistake import Mistake
from app.models.question import Question
from app.models.subject import Subject
from app.models.subtopic import SubTopic
from app.models.topic import Topic

logger = logging.getLogger(__name__)


class CampaignEngineRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Resolve subtopics from scope, grouped by subject ──

    async def get_subtopics_for_scope_grouped(
        self,
        subject_ids: list[UUID],
        topic_ids: list[UUID],
    ) -> list[dict]:
        """Returns list of {subject_id, subject_name, subtopics: [{subtopic_id, subtopic_name, topic_name, confidence_level}]}"""
        conditions = []
        if subject_ids:
            conditions.append(Topic.subject_id.in_(subject_ids))
        if topic_ids:
            conditions.append(Topic.id.in_(topic_ids))

        if not conditions:
            return []

        query = (
            select(
                SubTopic.id.label("subtopic_id"),
                SubTopic.name.label("subtopic_name"),
                SubTopic.confidence_level,
                Topic.name.label("topic_name"),
                Topic.subject_id,
                Subject.name.label("subject_name"),
            )
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(
                or_(*conditions),
                SubTopic.is_archived == False,
            )
            .order_by(
                Subject.order.asc(),
                Topic.order.asc(),
                SubTopic.order.asc(),
            )
        )
        result = await self.db.execute(query)
        rows = result.all()

        # Group by subject
        subjects_map: dict[str, dict] = {}
        for row in rows:
            sid = str(row.subject_id)
            if sid not in subjects_map:
                subjects_map[sid] = {
                    "subject_id": sid,
                    "subject_name": row.subject_name,
                    "subtopics": [],
                }
            subjects_map[sid]["subtopics"].append({
                "subtopic_id": str(row.subtopic_id),
                "subtopic_name": row.subtopic_name,
                "topic_name": row.topic_name,
                "subject_name": row.subject_name,
                "confidence_level": row.confidence_level,
            })

        return list(subjects_map.values())

    # ── Flat subtopics (kept for backward compat) ──

    async def get_subtopics_for_scope(
        self,
        subject_ids: list[UUID],
        topic_ids: list[UUID],
    ) -> list[dict]:
        conditions = []
        if subject_ids:
            conditions.append(Topic.subject_id.in_(subject_ids))
        if topic_ids:
            conditions.append(Topic.id.in_(topic_ids))

        if not conditions:
            return []

        query = (
            select(SubTopic.id, SubTopic.confidence_level, SubTopic.mastery_level)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .where(
                or_(*conditions),
                SubTopic.is_archived == False,
            )
            .order_by(SubTopic.confidence_level.asc(), SubTopic.last_revised_at.asc().nullsfirst())
        )
        result = await self.db.execute(query)
        return [{"subtopic_id": row.id} for row in result.all()]

    # ── Resolve mistakes from scope ──

    async def get_mistakes_for_scope(
        self,
        subject_ids: list[UUID],
        topic_ids: list[UUID],
    ) -> list[dict]:
        conditions = []
        if subject_ids:
            conditions.append(Topic.subject_id.in_(subject_ids))
        if topic_ids:
            conditions.append(Topic.id.in_(topic_ids))

        if not conditions:
            return []

        query = (
            select(Mistake.id, Mistake.subtopic_id)
            .join(SubTopic, Mistake.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .where(
                or_(*conditions),
                Mistake.is_resolved == False,
            )
            .order_by(Mistake.created_at.asc())
        )
        result = await self.db.execute(query)
        return [
            {"mistake_id": row.id, "subtopic_id": row.subtopic_id}
            for row in result.all()
        ]

    # ── Resolve PYQs from scope ──

    async def get_pyqs_for_scope(
        self,
        subject_ids: list[UUID],
        topic_ids: list[UUID],
    ) -> list[dict]:
        conditions = []
        if subject_ids:
            conditions.append(Topic.subject_id.in_(subject_ids))
        if topic_ids:
            conditions.append(Topic.id.in_(topic_ids))

        if not conditions:
            return []

        query = (
            select(Question.id, Question.subtopic_id)
            .join(SubTopic, Question.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .where(
                or_(*conditions),
                Question.is_pyq == True,
            )
            .order_by(Question.created_at.asc())
        )
        result = await self.db.execute(query)
        return [
            {"question_id": row.id, "subtopic_id": row.subtopic_id}
            for row in result.all()
        ]

    # ── Name lookups for enrichment ──

    async def get_scope_names(self, subject_id: UUID, topic_id: UUID | None) -> dict:
        result = {}
        sub_query = select(Subject.name).where(Subject.id == subject_id)
        sub_result = await self.db.execute(sub_query)
        result["subject_name"] = sub_result.scalar_one_or_none()

        if topic_id:
            topic_query = select(Topic.name).where(Topic.id == topic_id)
            topic_result = await self.db.execute(topic_query)
            result["topic_name"] = topic_result.scalar_one_or_none()
        else:
            result["topic_name"] = None

        return result

    async def get_item_names(
        self,
        subtopic_id: UUID | None = None,
        mistake_id: UUID | None = None,
        question_id: UUID | None = None,
    ) -> dict:
        result = {
            "subtopic_name": None,
            "topic_name": None,
            "subject_name": None,
            "mistake_description": None,
            "question_text": None,
        }

        if subtopic_id:
            query = (
                select(
                    SubTopic.name.label("subtopic_name"),
                    Topic.name.label("topic_name"),
                    Subject.name.label("subject_name"),
                )
                .join(Topic, SubTopic.topic_id == Topic.id)
                .join(Subject, Topic.subject_id == Subject.id)
                .where(SubTopic.id == subtopic_id)
            )
            row = (await self.db.execute(query)).first()
            if row:
                result["subtopic_name"] = row.subtopic_name
                result["topic_name"] = row.topic_name
                result["subject_name"] = row.subject_name

        if mistake_id:
            query = select(Mistake.description_html).where(Mistake.id == mistake_id)
            desc = (await self.db.execute(query)).scalar_one_or_none()
            result["mistake_description"] = desc

        if question_id:
            query = select(Question.text_html).where(Question.id == question_id)
            text = (await self.db.execute(query)).scalar_one_or_none()
            result["question_text"] = text

        return result
