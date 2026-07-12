from dataclasses import dataclass


@dataclass
class RegisterUserInput:
    username: str
    email: str
    password: str
