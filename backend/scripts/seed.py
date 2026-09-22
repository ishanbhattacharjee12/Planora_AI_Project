import asyncio
import sys

from sqlalchemy import select

from app.auth.security import hash_password
from app.database import async_session, engine, Base
from app.db_migrations import sync_missing_columns
from app.models import Department, EmployeeSkill, Skill, SkillLevel, User, UserRole


SKILLS = [
    ("Python", "backend"),
    ("FastAPI", "backend"),
    ("React", "frontend"),
    ("TypeScript", "frontend"),
    ("PostgreSQL", "database"),
    ("Docker", "devops"),
    ("Cybersecurity", "security"),
    ("REST APIs", "backend"),
    ("Git", "tools"),
    ("RAG", "ai"),
]

USERS = [
    ("admin@planora.local", "Admin User", UserRole.ADMIN, "admin123"),
    ("manager1@planora.local", "Manager One", UserRole.MANAGER, "manager123"),
    ("manager2@planora.local", "Manager Two", UserRole.MANAGER, "manager123"),
    ("alice@planora.local", "Alice Dev", UserRole.EMPLOYEE, "employee123"),
    ("bob@planora.local", "Bob Dev", UserRole.EMPLOYEE, "employee123"),
    ("carol@planora.local", "Carol Dev", UserRole.EMPLOYEE, "employee123"),
    ("dave@planora.local", "Dave Dev", UserRole.EMPLOYEE, "employee123"),
    ("eve@planora.local", "Eve Dev", UserRole.EMPLOYEE, "employee123"),
]

EMPLOYEE_SKILLS = {
    "alice@planora.local": [("Python", SkillLevel.ADVANCED), ("FastAPI", SkillLevel.ADVANCED), ("PostgreSQL", SkillLevel.INTERMEDIATE), ("Cybersecurity", SkillLevel.ADVANCED)],
    "bob@planora.local": [("React", SkillLevel.ADVANCED), ("TypeScript", SkillLevel.ADVANCED), ("REST APIs", SkillLevel.INTERMEDIATE)],
    "carol@planora.local": [("Python", SkillLevel.INTERMEDIATE), ("Docker", SkillLevel.INTERMEDIATE), ("PostgreSQL", SkillLevel.INTERMEDIATE)],
    "dave@planora.local": [("Cybersecurity", SkillLevel.EXPERT), ("Python", SkillLevel.INTERMEDIATE), ("RAG", SkillLevel.INTERMEDIATE)],
    "eve@planora.local": [("React", SkillLevel.INTERMEDIATE), ("Python", SkillLevel.BEGINNER), ("Git", SkillLevel.INTERMEDIATE)],
}


async def seed():
    async with engine.begin() as conn:
        if "postgresql" in str(engine.url):
            await conn.execute(__import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        if str(engine.url).startswith("sqlite"):
            await conn.run_sync(sync_missing_columns)

    async with async_session() as db:
        legacy_users = (await db.execute(select(User).where(User.email.like("%@projectintel.local")))).scalars().all()
        for user in legacy_users:
            user.email = f"{user.email.split('@', 1)[0]}@planora.local"
        if legacy_users:
            await db.commit()
            print(f"Migrated {len(legacy_users)} demo accounts to @planora.local.")

        existing = await db.execute(select(User).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded.")
            return

        dept = Department(name="Engineering", description="Software Engineering")
        db.add(dept)
        await db.flush()

        skill_map = {}
        for name, category in SKILLS:
            skill = Skill(name=name, category=category)
            db.add(skill)
            await db.flush()
            skill_map[name] = skill.id

        user_map = {}
        for email, full_name, role, password in USERS:
            user = User(
                email=email,
                full_name=full_name,
                role=role,
                hashed_password=hash_password(password),
                department_id=dept.id,
                capacity_percent=100,
            )
            db.add(user)
            await db.flush()
            user_map[email] = user

        for email, skills in EMPLOYEE_SKILLS.items():
            user = user_map[email]
            for skill_name, level in skills:
                db.add(EmployeeSkill(user_id=user.id, skill_id=skill_map[skill_name], level=level, years_experience=2.0))

        await db.commit()
        print("Seed complete!")
        print("Login: manager1@planora.local / manager123")
        print("Admin: admin@planora.local / admin123")
        print("Employee: alice@planora.local / employee123")


if __name__ == "__main__":
    asyncio.run(seed())
