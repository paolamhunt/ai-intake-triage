"""Domain models for incoming service inquiries."""

from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class CustomerContact(BaseModel):
    """Available information for returning to the prospective customer."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=50,
        pattern=r"^[0-9+().\-\s]+$",
    )


class InquirySource(BaseModel):
    """The channel through which an inquiry was received."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    channel: str = Field(min_length=1, max_length=50)
    external_reference: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )


class InquirySubmission(BaseModel):
    """A validated unstructured inquiry and its reply path."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    inquiry_text: str = Field(min_length=10, max_length=10_000)
    customer: CustomerContact
    source: InquirySource

    @model_validator(mode="after")
    def require_reply_path(self) -> Self:
        """Require contact details or a source reference for human follow-up."""
        if not (
            self.customer.email or self.customer.phone or self.source.external_reference
        ):
            raise ValueError(
                "At least one reply path is required: email, phone, "
                "or source external reference."
            )

        return self
