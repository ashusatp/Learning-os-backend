import logging
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.question_dependency import get_question_service
from app.schema.question_schema import (
    CreateQuestionRequest,
    UpdateQuestionRequest,
    ReorderQuestionsRequest,
    QuestionResponse,
)
from app.services.question_service import QuestionService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/subtopics/{subtopic_id}/questions",
    tags=["Questions"],
)


@router.post("", response_model=QuestionResponse, status_code=201)
async def create_question(
    subtopic_id: UUID,
    payload: CreateQuestionRequest,
    service: QuestionService = Depends(get_question_service),
):
    data = payload.model_dump()
    options = data.pop("options", [])
    return await service.create_question(
        subtopic_id=subtopic_id,
        options=options,
        **data,
    )


@router.get("", response_model=list[QuestionResponse])
async def get_questions(
    subtopic_id: UUID,
    service: QuestionService = Depends(get_question_service),
):
    return await service.get_questions_by_subtopic(subtopic_id)


@router.put("/reorder", response_model=list[QuestionResponse])
async def reorder_questions(
    subtopic_id: UUID,
    payload: ReorderQuestionsRequest,
    service: QuestionService = Depends(get_question_service),
):
    return await service.reorder_questions(subtopic_id, payload.ordered_ids)


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    subtopic_id: UUID,
    question_id: UUID,
    service: QuestionService = Depends(get_question_service),
):
    return await service.get_question(question_id)


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    subtopic_id: UUID,
    question_id: UUID,
    payload: UpdateQuestionRequest,
    service: QuestionService = Depends(get_question_service),
):
    data = payload.model_dump(exclude_unset=True)
    options = data.pop("options", None)
    if options is not None:
        return await service.update_question(question_id, options=options, **data)
    return await service.update_question(question_id, **data)


@router.delete("/{question_id}", status_code=204)
async def delete_question(
    subtopic_id: UUID,
    question_id: UUID,
    service: QuestionService = Depends(get_question_service),
):
    await service.delete_question(question_id)
