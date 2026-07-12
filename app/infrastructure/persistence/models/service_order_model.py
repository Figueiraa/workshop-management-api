from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.value_objects.service_order_status import ServiceOrderStatus
from app.infrastructure.database import Base


class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    status: Mapped[ServiceOrderStatus] = mapped_column(
        Enum(ServiceOrderStatus), nullable=False, default=ServiceOrderStatus.RECEBIDA
    )
    notes: Mapped[str | None] = mapped_column(Text)
    total_budget: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="service_orders")  # noqa: F821
    client: Mapped["Client"] = relationship("Client")  # noqa: F821
    items: Mapped[list["ServiceOrderItem"]] = relationship(
        "ServiceOrderItem", back_populates="service_order", cascade="all, delete-orphan"
    )
    parts: Mapped[list["ServiceOrderPart"]] = relationship(
        "ServiceOrderPart", back_populates="service_order", cascade="all, delete-orphan"
    )


class ServiceOrderItem(Base):
    __tablename__ = "service_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_order_id: Mapped[int] = mapped_column(ForeignKey("service_orders.id"), nullable=False)
    service_type_id: Mapped[int] = mapped_column(ForeignKey("service_types.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    service_order: Mapped["ServiceOrder"] = relationship("ServiceOrder", back_populates="items")
    service_type: Mapped["ServiceType"] = relationship("ServiceType")  # noqa: F821


class ServiceOrderPart(Base):
    __tablename__ = "service_order_parts"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_order_id: Mapped[int] = mapped_column(ForeignKey("service_orders.id"), nullable=False)
    part_id: Mapped[int] = mapped_column(ForeignKey("parts.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    service_order: Mapped["ServiceOrder"] = relationship("ServiceOrder", back_populates="parts")
    part: Mapped["Part"] = relationship("Part")  # noqa: F821
