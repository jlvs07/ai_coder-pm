from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CardCreate(ApiModel):
    title: str = Field(min_length=1, max_length=200)
    details: str = Field(default="", max_length=4000)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class CardUpdate(ApiModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    details: str | None = Field(default=None, max_length=4000)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value

    @model_validator(mode="after")
    def require_a_change(self) -> CardUpdate:
        if not self.model_fields_set:
            raise ValueError("provide title or details to update")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("updated values cannot be null")
        return self


class ColumnUpdate(ApiModel):
    title: str = Field(min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class ColumnCardOrder(ApiModel):
    columnId: str = Field(min_length=1)
    cardIds: list[str] = Field(max_length=500)


class BoardCardOrder(ApiModel):
    columns: list[ColumnCardOrder] = Field(max_length=100)
