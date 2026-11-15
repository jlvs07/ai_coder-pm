from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChatHistoryItem(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value


class BoardChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=20)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value


class ColumnRename(StrictModel):
    type: Literal["rename_column"]
    column_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class CardCreate(StrictModel):
    type: Literal["create_card"]
    column_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    details: str = Field(default="", max_length=4000)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class CardEdit(StrictModel):
    type: Literal["update_card"]
    card_id: str = Field(min_length=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    details: str | None = Field(default=None, max_length=4000)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value

    @model_validator(mode="after")
    def require_a_change(self) -> CardEdit:
        if not self.model_fields_set or any(
            getattr(self, field) is None for field in self.model_fields_set
        ):
            raise ValueError("provide a non-null title or details")
        return self


class CardMove(StrictModel):
    type: Literal["move_card"]
    card_id: str = Field(min_length=1)
    column_id: str = Field(min_length=1)
    position: int | None = Field(default=None, ge=0)


class CardDelete(StrictModel):
    type: Literal["delete_card"]
    card_id: str = Field(min_length=1)


BoardAction = Annotated[
    ColumnRename | CardCreate | CardEdit | CardMove | CardDelete,
    Field(discriminator="type"),
]


class BoardUpdate(StrictModel):
    actions: list[BoardAction] = Field(max_length=20)


class AIResponse(StrictModel):
    reply: str = Field(min_length=1, max_length=4000)
    board_update: BoardUpdate | None = None

    @field_validator("reply")
    @classmethod
    def reply_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("reply must not be blank")
        return value


class AIResponseError(Exception):
    pass
