from app.core.models import Role as CoreRole
from app.core.models import user_roles_table

# Re-export from core to maintain compatibility
Role = CoreRole
user_roles = user_roles_table

__all__ = ["Role", "user_roles"]
