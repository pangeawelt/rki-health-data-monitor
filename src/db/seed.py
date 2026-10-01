from sqlalchemy import select

from src.core.constants import AGE_GROUP_DISPLAY_NAMES, SUPPORTED_AGE_GROUPS
from src.db.models import AgeGroupModel


def seed_age_groups(session) -> None:  # noqa: ANN001
    existing = set(session.scalars(select(AgeGroupModel.age_group_code)).all())
    for index, code in enumerate(SUPPORTED_AGE_GROUPS):
        if code not in existing:
            session.add(
                AgeGroupModel(
                    age_group_code=code,
                    display_name=AGE_GROUP_DISPLAY_NAMES[code],
                    sort_order=index,
                )
            )
    session.flush()
