import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.career_catalog import CareerRole
from app.models.question import Question
from app.models.skill_catalog import SkillDefinition
from app.core.career_seed import SEED_CAREER_ROLES
from app.core.questions_seed import SEED_QUESTIONS
from app.core.skill_seed import SEED_SKILL_DEFINITIONS

logger = logging.getLogger(__name__)


async def seed_database(db: AsyncSession) -> None:
    """Populates career catalog, assessment questions, and skill definitions taxonomy if not present."""
    # 1. Seed Career Roles
    roles_count = (await db.execute(select(func.count(CareerRole.id)))).scalar() or 0
    if roles_count == 0:
        logger.info("Seeding career roles catalog...")
        for role_data in SEED_CAREER_ROLES:
            role = CareerRole(**role_data)
            db.add(role)
        await db.commit()
        logger.info(f"Seeded {len(SEED_CAREER_ROLES)} career roles.")

    # 2. Seed Assessment Questions
    questions_count = (await db.execute(select(func.count(Question.id)))).scalar() or 0
    if questions_count == 0:
        logger.info("Seeding assessment questions...")
        for q_data in SEED_QUESTIONS:
            q = Question(**q_data)
            db.add(q)
        await db.commit()
        logger.info(f"Seeded {len(SEED_QUESTIONS)} assessment questions.")

    # 3. Seed Skill Definitions Taxonomy
    skills_count = (await db.execute(select(func.count(SkillDefinition.id)))).scalar() or 0
    if skills_count == 0:
        logger.info("Seeding skill taxonomy definitions catalog...")
        for s_data in SEED_SKILL_DEFINITIONS:
            sdef = SkillDefinition(**s_data)
            db.add(sdef)
        await db.commit()
        logger.info(f"Seeded {len(SEED_SKILL_DEFINITIONS)} skill definitions.")
