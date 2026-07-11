from dataclasses import dataclass, field


@dataclass
class OpenServiceOrderItemInput:
    service_type_id: int
    quantity: int = 1


@dataclass
class OpenServiceOrderPartInput:
    part_id: int
    quantity: int = 1


@dataclass
class OpenServiceOrderInput:
    vehicle_id: int
    notes: str | None = None
    items: list[OpenServiceOrderItemInput] = field(default_factory=list)
    parts: list[OpenServiceOrderPartInput] = field(default_factory=list)


@dataclass
class AverageExecutionTimeResult:
    average_minutes: float | None
    total_completed: int
