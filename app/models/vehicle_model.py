from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    plate: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    client: Mapped["Client"] = relationship("Client", back_populates="vehicles")  # noqa: F821
    service_orders: Mapped[list["ServiceOrder"]] = relationship("ServiceOrder", back_populates="vehicle")  # noqa: F821
