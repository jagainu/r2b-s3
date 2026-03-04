import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# ---------------------------------------------------------------------------
# マスター3種：coat_colors / coat_patterns / coat_lengths
# ---------------------------------------------------------------------------


class CoatColor(Base):
    __tablename__ = "coat_colors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    cat_breeds: Mapped[list["CatBreed"]] = relationship(back_populates="coat_color")


class CoatPattern(Base):
    __tablename__ = "coat_patterns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    cat_breeds: Mapped[list["CatBreed"]] = relationship(back_populates="coat_pattern")


class CoatLength(Base):
    __tablename__ = "coat_lengths"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    cat_breeds: Mapped[list["CatBreed"]] = relationship(back_populates="coat_length")


# ---------------------------------------------------------------------------
# cat_breeds（猫種）
# ---------------------------------------------------------------------------


class CatBreed(Base):
    __tablename__ = "cat_breeds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    coat_color_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("coat_colors.id"),
        nullable=False,
    )
    coat_pattern_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("coat_patterns.id"),
        nullable=False,
    )
    coat_length_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("coat_lengths.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    coat_color: Mapped["CoatColor"] = relationship(back_populates="cat_breeds")
    coat_pattern: Mapped["CoatPattern"] = relationship(back_populates="cat_breeds")
    coat_length: Mapped["CoatLength"] = relationship(back_populates="cat_breeds")
    photos: Mapped[list["CatPhoto"]] = relationship(
        back_populates="cat_breed", cascade="all, delete-orphan"
    )
    similar_as_source: Mapped[list["SimilarCat"]] = relationship(
        foreign_keys="SimilarCat.cat_breed_id",
        back_populates="cat_breed",
        cascade="all, delete-orphan",
    )
    similar_as_target: Mapped[list["SimilarCat"]] = relationship(
        foreign_keys="SimilarCat.similar_cat_breed_id",
        back_populates="similar_cat_breed",
    )

    __table_args__ = (
        Index("idx_cat_breeds_coat_color", "coat_color_id"),
        Index("idx_cat_breeds_coat_pattern", "coat_pattern_id"),
        Index("idx_cat_breeds_coat_length", "coat_length_id"),
    )


# ---------------------------------------------------------------------------
# cat_photos（猫写真）
# ---------------------------------------------------------------------------


class CatPhoto(Base):
    __tablename__ = "cat_photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    cat_breed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cat_breeds.id"),
        nullable=False,
    )
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    cat_breed: Mapped["CatBreed"] = relationship(back_populates="photos")

    __table_args__ = (Index("idx_cat_photos_breed", "cat_breed_id", "display_order"),)


# ---------------------------------------------------------------------------
# similar_cats（類似猫）
# ---------------------------------------------------------------------------


class SimilarCat(Base):
    __tablename__ = "similar_cats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    cat_breed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cat_breeds.id"),
        nullable=False,
    )
    similar_cat_breed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cat_breeds.id"),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    cat_breed: Mapped["CatBreed"] = relationship(
        foreign_keys=[cat_breed_id],
        back_populates="similar_as_source",
    )
    similar_cat_breed: Mapped["CatBreed"] = relationship(
        foreign_keys=[similar_cat_breed_id],
        back_populates="similar_as_target",
    )

    __table_args__ = (
        UniqueConstraint(
            "cat_breed_id", "similar_cat_breed_id", name="uq_similar_cats"
        ),
        CheckConstraint(
            "cat_breed_id <> similar_cat_breed_id", name="ck_similar_cats_no_self"
        ),
        Index("idx_similar_cats_breed", "cat_breed_id", "priority"),
    )
