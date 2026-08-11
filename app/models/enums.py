from enum import Enum


class StandardRoles(Enum):
    """Papéis padrão do sistema (imutáveis)."""

    USER = "User"
    MANAGER = "Manager"
    ADMIN = "Admin"
