"""
Service Academic
=================

Logique métier pour la gestion des programmes et formations.
"""

from uuid import uuid4

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.academic import (
    Program,
    ProgramCampus,
    ProgramCareerOpportunity,
    ProgramCourse,
    ProgramField,
    ProgramPartner,
    ProgramSemester,
    ProgramSkill,
)
from app.models.base import PublicationStatus


class AcademicService:
    """Service pour la gestion des programmes et formations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # PROGRAMS
    # =========================================================================

    async def get_programs(
        self,
        search: str | None = None,
        program_type: str | None = None,
        sector_id: str | None = None,
        status: PublicationStatus | None = None,
        field_id: str | None = None,
    ) -> select:
        """
        Construit une requête pour lister les programmes.

        Args:
            search: Recherche sur code, titre ou description.
            program_type: Filtrer par type de programme.
            sector_id: Filtrer par département.
            status: Filtrer par statut de publication.
            field_id: Filtrer par champ disciplinaire.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Program).options(
            selectinload(Program.semesters).selectinload(ProgramSemester.courses),
            selectinload(Program.skills),
            selectinload(Program.career_opportunities),
        )

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Program.code.ilike(search_filter),
                    Program.title.ilike(search_filter),
                    Program.description.ilike(search_filter),
                )
            )

        if program_type:
            query = query.where(Program.type == program_type)

        if sector_id:
            query = query.where(Program.sector_external_id == sector_id)

        if status:
            query = query.where(Program.status == status)

        if field_id:
            query = query.where(Program.field_id == field_id)

        query = query.order_by(Program.display_order, Program.title)
        return query

    async def get_published_programs(
        self,
        search: str | None = None,
        program_type: str | None = None,
        sector_id: str | None = None,
        skip_order_by: bool = False,
    ) -> select:
        """
        Construit une requête pour lister les programmes publiés (public).

        Args:
            search: Recherche sur code, titre ou description.
            program_type: Filtrer par type de programme.
            sector_id: Filtrer par département.
            skip_order_by: Ne pas ajouter de clause ORDER BY (utile pour pagination).

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Program).options(
            selectinload(Program.semesters).selectinload(ProgramSemester.courses),
            selectinload(Program.skills),
            selectinload(Program.career_opportunities),
        ).where(Program.status == PublicationStatus.PUBLISHED)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Program.code.ilike(search_filter),
                    Program.title.ilike(search_filter),
                    Program.description.ilike(search_filter),
                )
            )

        if program_type:
            query = query.where(Program.type == program_type)

        if sector_id:
            query = query.where(Program.sector_external_id == sector_id)

        if not skip_order_by:
            query = query.order_by(Program.display_order, Program.title)
        return query

    async def get_featured_programs(self, limit: int = 4) -> list[Program]:
        """
        Récupère les programmes publiés mis à la une.

        Args:
            limit: Nombre maximum de programmes à retourner.

        Returns:
            Liste des programmes featured.
        """
        result = await self.db.execute(
            select(Program)
            .options(
                selectinload(Program.semesters).selectinload(ProgramSemester.courses),
                selectinload(Program.skills),
                selectinload(Program.career_opportunities),
            )
            .where(
                Program.status == PublicationStatus.PUBLISHED,
                Program.is_featured == True,  # noqa: E712
            )
            .order_by(Program.display_order, Program.title)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_program_by_id(self, program_id: str) -> Program | None:
        """Récupère un programme par son ID."""
        result = await self.db.execute(
            select(Program)
            .options(
                selectinload(Program.semesters).selectinload(ProgramSemester.courses),
                selectinload(Program.skills),
                selectinload(Program.career_opportunities),
            )
            .where(Program.id == program_id)
        )
        return result.scalar_one_or_none()

    async def get_program_by_slug(self, slug: str) -> Program | None:
        """Récupère un programme par son slug."""
        result = await self.db.execute(
            select(Program)
            .options(
                selectinload(Program.semesters).selectinload(ProgramSemester.courses),
                selectinload(Program.skills),
                selectinload(Program.career_opportunities),
            )
            .where(Program.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_program_by_code(self, code: str) -> Program | None:
        """Récupère un programme par son code."""
        result = await self.db.execute(
            select(Program).where(Program.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def create_program(
        self,
        code: str,
        title: str,
        slug: str,
        type: str,
        **kwargs,
    ) -> Program:
        """
        Crée un nouveau programme.

        Args:
            code: Code unique du programme.
            title: Titre du programme.
            slug: Slug URL du programme.
            type: Type de programme.
            **kwargs: Autres champs optionnels.

        Returns:
            Programme créé.

        Raises:
            ConflictException: Si le code ou le slug existe déjà.
        """
        code = code.upper()
        existing_code = await self.get_program_by_code(code)
        if existing_code:
            raise ConflictException(f"Un programme avec le code '{code}' existe déjà")

        existing_slug = await self.get_program_by_slug(slug)
        if existing_slug:
            raise ConflictException(f"Un programme avec le slug '{slug}' existe déjà")

        program = Program(
            id=str(uuid4()),
            code=code,
            title=title,
            slug=slug,
            type=type,
            **kwargs,
        )
        self.db.add(program)
        await self.db.flush()
        return program

    async def update_program(self, program_id: str, **kwargs) -> Program:
        """
        Met à jour un programme.

        Args:
            program_id: ID du programme.
            **kwargs: Champs à mettre à jour.

        Returns:
            Programme mis à jour.

        Raises:
            NotFoundException: Si le programme n'existe pas.
            ConflictException: Si le nouveau code ou slug existe déjà.
        """
        program = await self.get_program_by_id(program_id)
        if not program:
            raise NotFoundException("Programme non trouvé")

        # Vérifier l'unicité du code si modifié
        if "code" in kwargs and kwargs["code"]:
            kwargs["code"] = kwargs["code"].upper()
            if kwargs["code"] != program.code:
                existing = await self.get_program_by_code(kwargs["code"])
                if existing:
                    raise ConflictException(
                        f"Un programme avec le code '{kwargs['code']}' existe déjà"
                    )

        # Vérifier l'unicité du slug si modifié
        if "slug" in kwargs and kwargs["slug"]:
            if kwargs["slug"] != program.slug:
                existing = await self.get_program_by_slug(kwargs["slug"])
                if existing:
                    raise ConflictException(
                        f"Un programme avec le slug '{kwargs['slug']}' existe déjà"
                    )

        await self.db.execute(
            update(Program).where(Program.id == program_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_program_by_id(program_id)

    async def delete_program(self, program_id: str) -> None:
        """
        Supprime un programme.

        Args:
            program_id: ID du programme.

        Raises:
            NotFoundException: Si le programme n'existe pas.
        """
        program = await self.get_program_by_id(program_id)
        if not program:
            raise NotFoundException("Programme non trouvé")

        await self.db.execute(delete(Program).where(Program.id == program_id))
        await self.db.flush()

    async def toggle_program_status(
        self, program_id: str, status: PublicationStatus
    ) -> Program:
        """Change le statut de publication d'un programme."""
        program = await self.get_program_by_id(program_id)
        if not program:
            raise NotFoundException("Programme non trouvé")

        await self.db.execute(
            update(Program).where(Program.id == program_id).values(status=status)
        )
        await self.db.flush()
        return await self.get_program_by_id(program_id)

    async def duplicate_program(
        self, program_id: str, new_code: str, new_title: str, new_slug: str
    ) -> Program:
        """
        Duplique un programme existant.

        Args:
            program_id: ID du programme à dupliquer.
            new_code: Nouveau code.
            new_title: Nouveau titre.
            new_slug: Nouveau slug.

        Returns:
            Nouveau programme créé.

        Raises:
            NotFoundException: Si le programme n'existe pas.
            ConflictException: Si le nouveau code ou slug existe déjà.
        """
        program = await self.get_program_by_id(program_id)
        if not program:
            raise NotFoundException("Programme non trouvé")

        # Créer le nouveau programme
        new_program = await self.create_program(
            code=new_code,
            title=new_title,
            slug=new_slug,
            type=program.type,
            subtitle=program.subtitle,
            description=program.description,
            teaching_methods=program.teaching_methods,
            cover_image_external_id=program.cover_image_external_id,
            sector_external_id=program.sector_external_id,
            coordinator_external_id=program.coordinator_external_id,
            field_id=program.field_id,
            duration_months=program.duration_months,
            credits=program.credits,
            degree_awarded=program.degree_awarded,
            required_degree=program.required_degree,
            status=PublicationStatus.DRAFT,
            display_order=program.display_order,
        )

        # Dupliquer les semestres et cours
        for semester in program.semesters:
            new_semester = ProgramSemester(
                id=str(uuid4()),
                program_id=new_program.id,
                number=semester.number,
                title=semester.title,
                credits=semester.credits,
                display_order=semester.display_order,
            )
            self.db.add(new_semester)
            await self.db.flush()

            for course in semester.courses:
                new_course = ProgramCourse(
                    id=str(uuid4()),
                    semester_id=new_semester.id,
                    code=course.code,
                    title=course.title,
                    description=course.description,
                    credits=course.credits,
                    lecture_hours=course.lecture_hours,
                    tutorial_hours=course.tutorial_hours,
                    practical_hours=course.practical_hours,
                    coefficient=course.coefficient,
                    display_order=course.display_order,
                )
                self.db.add(new_course)

        # Dupliquer les compétences
        for skill in program.skills:
            new_skill = ProgramSkill(
                id=str(uuid4()),
                program_id=new_program.id,
                title=skill.title,
                description=skill.description,
                display_order=skill.display_order,
            )
            self.db.add(new_skill)

        # Dupliquer les débouchés
        for opportunity in program.career_opportunities:
            new_opportunity = ProgramCareerOpportunity(
                id=str(uuid4()),
                program_id=new_program.id,
                title=opportunity.title,
                description=opportunity.description,
                display_order=opportunity.display_order,
            )
            self.db.add(new_opportunity)

        await self.db.flush()
        return await self.get_program_by_id(new_program.id)

    async def reorder_programs(self, program_ids: list[str]) -> list[Program]:
        """
        Réordonne les programmes.

        Args:
            program_ids: Liste ordonnée des IDs de programmes.

        Returns:
            Liste des programmes réordonnés.
        """
        for index, program_id in enumerate(program_ids):
            await self.db.execute(
                update(Program).where(Program.id == program_id).values(display_order=index)
            )
        await self.db.flush()

        result = await self.db.execute(
            select(Program)
            .where(Program.id.in_(program_ids))
            .order_by(Program.display_order)
        )
        return list(result.scalars().all())

    # =========================================================================
    # PROGRAM FIELDS (Champs disciplinaires)
    # =========================================================================

    async def get_fields(self) -> select:
        """Construit une requête pour lister les champs disciplinaires."""
        return select(ProgramField).order_by(
            ProgramField.display_order, ProgramField.name
        )

    async def get_field_by_id(self, field_id: str) -> ProgramField | None:
        """Récupère un champ par son ID."""
        result = await self.db.execute(
            select(ProgramField).where(ProgramField.id == field_id)
        )
        return result.scalar_one_or_none()

    async def get_field_by_slug(self, slug: str) -> ProgramField | None:
        """Récupère un champ par son slug."""
        result = await self.db.execute(
            select(ProgramField).where(ProgramField.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_field(
        self,
        name: str,
        slug: str,
        **kwargs,
    ) -> ProgramField:
        """Crée un nouveau champ disciplinaire."""
        existing = await self.get_field_by_slug(slug)
        if existing:
            raise ConflictException(f"Un champ avec le slug '{slug}' existe déjà")

        field = ProgramField(
            id=str(uuid4()),
            name=name,
            slug=slug,
            **kwargs,
        )
        self.db.add(field)
        await self.db.flush()
        return field

    async def update_field(self, field_id: str, **kwargs) -> ProgramField:
        """Met à jour un champ disciplinaire."""
        field = await self.get_field_by_id(field_id)
        if not field:
            raise NotFoundException("Champ non trouvé")

        # Vérifier l'unicité du slug si modifié
        if "slug" in kwargs and kwargs["slug"] and kwargs["slug"] != field.slug:
            existing = await self.get_field_by_slug(kwargs["slug"])
            if existing:
                raise ConflictException(
                    f"Un champ avec le slug '{kwargs['slug']}' existe déjà"
                )

        await self.db.execute(
            update(ProgramField).where(ProgramField.id == field_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_field_by_id(field_id)

    async def delete_field(self, field_id: str) -> None:
        """Supprime un champ disciplinaire."""
        field = await self.get_field_by_id(field_id)
        if not field:
            raise NotFoundException("Champ non trouvé")

        await self.db.execute(
            delete(ProgramField).where(ProgramField.id == field_id)
        )
        await self.db.flush()

    async def reorder_fields(self, field_ids: list[str]) -> list[ProgramField]:
        """Réordonne les champs disciplinaires."""
        for index, field_id in enumerate(field_ids):
            await self.db.execute(
                update(ProgramField)
                .where(ProgramField.id == field_id)
                .values(display_order=index)
            )
        await self.db.flush()

        result = await self.db.execute(
            select(ProgramField)
            .where(ProgramField.id.in_(field_ids))
            .order_by(ProgramField.display_order)
        )
        return list(result.scalars().all())

    # =========================================================================
    # PROGRAM SEMESTERS
    # =========================================================================

    async def get_semesters(
        self,
        program_id: str | None = None,
    ) -> select:
        """
        Construit une requête pour lister les semestres.

        Args:
            program_id: Filtrer par programme.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(ProgramSemester).options(
            selectinload(ProgramSemester.courses)
        )

        if program_id:
            query = query.where(ProgramSemester.program_id == program_id)

        query = query.order_by(ProgramSemester.display_order, ProgramSemester.number)
        return query

    async def get_semester_by_id(self, semester_id: str) -> ProgramSemester | None:
        """Récupère un semestre par son ID."""
        result = await self.db.execute(
            select(ProgramSemester)
            .options(selectinload(ProgramSemester.courses))
            .where(ProgramSemester.id == semester_id)
        )
        return result.scalar_one_or_none()

    async def create_semester(
        self,
        program_id: str,
        number: int,
        **kwargs,
    ) -> ProgramSemester:
        """
        Crée un nouveau semestre.

        Args:
            program_id: ID du programme.
            number: Numéro du semestre.
            **kwargs: Autres champs optionnels.

        Returns:
            Semestre créé.

        Raises:
            NotFoundException: Si le programme n'existe pas.
            ConflictException: Si le numéro de semestre existe déjà.
        """
        program = await self.get_program_by_id(program_id)
        if not program:
            raise NotFoundException("Programme non trouvé")

        # Vérifier l'unicité du numéro
        result = await self.db.execute(
            select(ProgramSemester).where(
                ProgramSemester.program_id == program_id,
                ProgramSemester.number == number,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException(f"Le semestre {number} existe déjà pour ce programme")

        semester = ProgramSemester(
            id=str(uuid4()),
            program_id=program_id,
            number=number,
            **kwargs,
        )
        self.db.add(semester)
        await self.db.flush()
        return semester

    async def update_semester(self, semester_id: str, **kwargs) -> ProgramSemester:
        """
        Met à jour un semestre.

        Args:
            semester_id: ID du semestre.
            **kwargs: Champs à mettre à jour.

        Returns:
            Semestre mis à jour.

        Raises:
            NotFoundException: Si le semestre n'existe pas.
            ConflictException: Si le nouveau numéro existe déjà.
        """
        semester = await self.get_semester_by_id(semester_id)
        if not semester:
            raise NotFoundException("Semestre non trouvé")

        # Vérifier l'unicité du numéro si modifié
        if "number" in kwargs and kwargs["number"] != semester.number:
            result = await self.db.execute(
                select(ProgramSemester).where(
                    ProgramSemester.program_id == semester.program_id,
                    ProgramSemester.number == kwargs["number"],
                    ProgramSemester.id != semester_id,
                )
            )
            if result.scalar_one_or_none():
                raise ConflictException(
                    f"Le semestre {kwargs['number']} existe déjà pour ce programme"
                )

        await self.db.execute(
            update(ProgramSemester).where(ProgramSemester.id == semester_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_semester_by_id(semester_id)

    async def delete_semester(self, semester_id: str) -> None:
        """
        Supprime un semestre.

        Args:
            semester_id: ID du semestre.

        Raises:
            NotFoundException: Si le semestre n'existe pas.
        """
        semester = await self.get_semester_by_id(semester_id)
        if not semester:
            raise NotFoundException("Semestre non trouvé")

        await self.db.execute(
            delete(ProgramSemester).where(ProgramSemester.id == semester_id)
        )
        await self.db.flush()

    # =========================================================================
    # PROGRAM COURSES
    # =========================================================================

    async def get_semester_courses(self, semester_id: str) -> list[ProgramCourse]:
        """Récupère les cours d'un semestre."""
        semester = await self.get_semester_by_id(semester_id)
        if not semester:
            raise NotFoundException("Semestre non trouvé")

        result = await self.db.execute(
            select(ProgramCourse)
            .where(ProgramCourse.semester_id == semester_id)
            .order_by(ProgramCourse.display_order)
        )
        return list(result.scalars().all())

    async def get_course_by_id(self, course_id: str) -> ProgramCourse | None:
        """Récupère un cours par son ID."""
        result = await self.db.execute(
            select(ProgramCourse).where(ProgramCourse.id == course_id)
        )
        return result.scalar_one_or_none()

    async def create_course(
        self,
        semester_id: str,
        title: str,
        **kwargs,
    ) -> ProgramCourse:
        """
        Crée un nouveau cours.

        Args:
            semester_id: ID du semestre.
            title: Titre du cours.
            **kwargs: Autres champs optionnels.

        Returns:
            Cours créé.

        Raises:
            NotFoundException: Si le semestre n'existe pas.
        """
        semester = await self.get_semester_by_id(semester_id)
        if not semester:
            raise NotFoundException("Semestre non trouvé")

        course = ProgramCourse(
            id=str(uuid4()),
            semester_id=semester_id,
            title=title,
            **kwargs,
        )
        self.db.add(course)
        await self.db.flush()
        return course

    async def update_course(self, course_id: str, **kwargs) -> ProgramCourse:
        """
        Met à jour un cours.

        Args:
            course_id: ID du cours.
            **kwargs: Champs à mettre à jour.

        Returns:
            Cours mis à jour.

        Raises:
            NotFoundException: Si le cours n'existe pas.
        """
        course = await self.get_course_by_id(course_id)
        if not course:
            raise NotFoundException("Cours non trouvé")

        await self.db.execute(
            update(ProgramCourse).where(ProgramCourse.id == course_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_course_by_id(course_id)

    async def delete_course(self, course_id: str) -> None:
        """
        Supprime un cours.

        Args:
            course_id: ID du cours.

        Raises:
            NotFoundException: Si le cours n'existe pas.
        """
        course = await self.get_course_by_id(course_id)
        if not course:
            raise NotFoundException("Cours non trouvé")

        await self.db.execute(
            delete(ProgramCourse).where(ProgramCourse.id == course_id)
        )
        await self.db.flush()

    async def reorder_courses(self, course_ids: list[str]) -> list[ProgramCourse]:
        """
        Réordonne les cours.

        Args:
            course_ids: Liste ordonnée des IDs de cours.

        Returns:
            Liste des cours réordonnés.
        """
        for index, course_id in enumerate(course_ids):
            await self.db.execute(
                update(ProgramCourse)
                .where(ProgramCourse.id == course_id)
                .values(display_order=index)
            )
        await self.db.flush()

        result = await self.db.execute(
            select(ProgramCourse)
            .where(ProgramCourse.id.in_(course_ids))
            .order_by(ProgramCourse.display_order)
        )
        return list(result.scalars().all())

    # =========================================================================
    # PROGRAM SKILLS
    # =========================================================================

    async def get_skills(
        self,
        program_id: str | None = None,
    ) -> select:
        """
        Construit une requête pour lister les compétences.

        Args:
            program_id: Filtrer par programme.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(ProgramSkill)

        if program_id:
            query = query.where(ProgramSkill.program_id == program_id)

        query = query.order_by(ProgramSkill.display_order)
        return query

    async def get_skill_by_id(self, skill_id: str) -> ProgramSkill | None:
        """Récupère une compétence par son ID."""
        result = await self.db.execute(
            select(ProgramSkill).where(ProgramSkill.id == skill_id)
        )
        return result.scalar_one_or_none()

    async def create_skill(
        self,
        program_id: str,
        title: str,
        **kwargs,
    ) -> ProgramSkill:
        """
        Crée une nouvelle compétence.

        Args:
            program_id: ID du programme.
            title: Titre de la compétence.
            **kwargs: Autres champs optionnels.

        Returns:
            Compétence créée.

        Raises:
            NotFoundException: Si le programme n'existe pas.
        """
        program = await self.get_program_by_id(program_id)
        if not program:
            raise NotFoundException("Programme non trouvé")

        skill = ProgramSkill(
            id=str(uuid4()),
            program_id=program_id,
            title=title,
            **kwargs,
        )
        self.db.add(skill)
        await self.db.flush()
        return skill

    async def update_skill(self, skill_id: str, **kwargs) -> ProgramSkill:
        """
        Met à jour une compétence.

        Args:
            skill_id: ID de la compétence.
            **kwargs: Champs à mettre à jour.

        Returns:
            Compétence mise à jour.

        Raises:
            NotFoundException: Si la compétence n'existe pas.
        """
        skill = await self.get_skill_by_id(skill_id)
        if not skill:
            raise NotFoundException("Compétence non trouvée")

        await self.db.execute(
            update(ProgramSkill).where(ProgramSkill.id == skill_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_skill_by_id(skill_id)

    async def delete_skill(self, skill_id: str) -> None:
        """
        Supprime une compétence.

        Args:
            skill_id: ID de la compétence.

        Raises:
            NotFoundException: Si la compétence n'existe pas.
        """
        skill = await self.get_skill_by_id(skill_id)
        if not skill:
            raise NotFoundException("Compétence non trouvée")

        await self.db.execute(
            delete(ProgramSkill).where(ProgramSkill.id == skill_id)
        )
        await self.db.flush()

    async def reorder_skills(self, skill_ids: list[str]) -> list[ProgramSkill]:
        """
        Réordonne les compétences.

        Args:
            skill_ids: Liste ordonnée des IDs de compétences.

        Returns:
            Liste des compétences réordonnées.
        """
        for index, skill_id in enumerate(skill_ids):
            await self.db.execute(
                update(ProgramSkill)
                .where(ProgramSkill.id == skill_id)
                .values(display_order=index)
            )
        await self.db.flush()

        result = await self.db.execute(
            select(ProgramSkill)
            .where(ProgramSkill.id.in_(skill_ids))
            .order_by(ProgramSkill.display_order)
        )
        return list(result.scalars().all())

    # =========================================================================
    # PROGRAM CAREER OPPORTUNITIES
    # =========================================================================

    async def get_career_opportunities(
        self,
        program_id: str | None = None,
    ) -> select:
        """
        Construit une requête pour lister les débouchés.

        Args:
            program_id: Filtrer par programme.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(ProgramCareerOpportunity)

        if program_id:
            query = query.where(ProgramCareerOpportunity.program_id == program_id)

        query = query.order_by(ProgramCareerOpportunity.display_order)
        return query

    async def get_career_opportunity_by_id(
        self, opportunity_id: str
    ) -> ProgramCareerOpportunity | None:
        """Récupère un débouché par son ID."""
        result = await self.db.execute(
            select(ProgramCareerOpportunity).where(
                ProgramCareerOpportunity.id == opportunity_id
            )
        )
        return result.scalar_one_or_none()

    async def create_career_opportunity(
        self,
        program_id: str,
        title: str,
        **kwargs,
    ) -> ProgramCareerOpportunity:
        """
        Crée un nouveau débouché.

        Args:
            program_id: ID du programme.
            title: Titre du débouché.
            **kwargs: Autres champs optionnels.

        Returns:
            Débouché créé.

        Raises:
            NotFoundException: Si le programme n'existe pas.
        """
        program = await self.get_program_by_id(program_id)
        if not program:
            raise NotFoundException("Programme non trouvé")

        opportunity = ProgramCareerOpportunity(
            id=str(uuid4()),
            program_id=program_id,
            title=title,
            **kwargs,
        )
        self.db.add(opportunity)
        await self.db.flush()
        return opportunity

    async def update_career_opportunity(
        self, opportunity_id: str, **kwargs
    ) -> ProgramCareerOpportunity:
        """
        Met à jour un débouché.

        Args:
            opportunity_id: ID du débouché.
            **kwargs: Champs à mettre à jour.

        Returns:
            Débouché mis à jour.

        Raises:
            NotFoundException: Si le débouché n'existe pas.
        """
        opportunity = await self.get_career_opportunity_by_id(opportunity_id)
        if not opportunity:
            raise NotFoundException("Débouché non trouvé")

        await self.db.execute(
            update(ProgramCareerOpportunity)
            .where(ProgramCareerOpportunity.id == opportunity_id)
            .values(**kwargs)
        )
        await self.db.flush()
        return await self.get_career_opportunity_by_id(opportunity_id)

    async def delete_career_opportunity(self, opportunity_id: str) -> None:
        """
        Supprime un débouché.

        Args:
            opportunity_id: ID du débouché.

        Raises:
            NotFoundException: Si le débouché n'existe pas.
        """
        opportunity = await self.get_career_opportunity_by_id(opportunity_id)
        if not opportunity:
            raise NotFoundException("Débouché non trouvé")

        await self.db.execute(
            delete(ProgramCareerOpportunity).where(
                ProgramCareerOpportunity.id == opportunity_id
            )
        )
        await self.db.flush()

    async def reorder_career_opportunities(
        self, opportunity_ids: list[str]
    ) -> list[ProgramCareerOpportunity]:
        """
        Réordonne les débouchés.

        Args:
            opportunity_ids: Liste ordonnée des IDs de débouchés.

        Returns:
            Liste des débouchés réordonnés.
        """
        for index, opportunity_id in enumerate(opportunity_ids):
            await self.db.execute(
                update(ProgramCareerOpportunity)
                .where(ProgramCareerOpportunity.id == opportunity_id)
                .values(display_order=index)
            )
        await self.db.flush()

        result = await self.db.execute(
            select(ProgramCareerOpportunity)
            .where(ProgramCareerOpportunity.id.in_(opportunity_ids))
            .order_by(ProgramCareerOpportunity.display_order)
        )
        return list(result.scalars().all())

    # =========================================================================
    # PROGRAM CAMPUSES
    # =========================================================================

    async def get_program_campuses(self, program_id: str) -> list[str]:
        """Récupère les IDs de campus d'un programme."""
        program = await self.get_program_by_id(program_id)
        if not program:
            raise NotFoundException("Programme non trouvé")

        result = await self.db.execute(
            select(ProgramCampus.campus_external_id).where(
                ProgramCampus.program_id == program_id
            )
        )
        return [row[0] for row in result.all()]

    async def add_campus_to_program(
        self, program_id: str, campus_external_id: str
    ) -> None:
        """
        Ajoute un campus à un programme.

        Args:
            program_id: ID du programme.
            campus_external_id: ID du campus.

        Raises:
            NotFoundException: Si le programme n'existe pas.
            ConflictException: Si le campus est déjà associé.
        """
        program = await self.get_program_by_id(program_id)
        if not program:
            raise NotFoundException("Programme non trouvé")

        # Vérifier si la liaison existe déjà
        result = await self.db.execute(
            select(ProgramCampus).where(
                ProgramCampus.program_id == program_id,
                ProgramCampus.campus_external_id == campus_external_id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Ce campus est déjà associé au programme")

        link = ProgramCampus(
            program_id=program_id,
            campus_external_id=campus_external_id,
        )
        self.db.add(link)
        await self.db.flush()

    async def remove_campus_from_program(
        self, program_id: str, campus_external_id: str
    ) -> None:
        """
        Retire un campus d'un programme.

        Args:
            program_id: ID du programme.
            campus_external_id: ID du campus.

        Raises:
            NotFoundException: Si l'association n'existe pas.
        """
        result = await self.db.execute(
            select(ProgramCampus).where(
                ProgramCampus.program_id == program_id,
                ProgramCampus.campus_external_id == campus_external_id,
            )
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Cette association n'existe pas")

        await self.db.execute(
            delete(ProgramCampus).where(
                ProgramCampus.program_id == program_id,
                ProgramCampus.campus_external_id == campus_external_id,
            )
        )
        await self.db.flush()

    # =========================================================================
    # PROGRAM PARTNERS
    # =========================================================================

    async def get_program_partners(self, program_id: str) -> list[ProgramPartner]:
        """Récupère les partenaires d'un programme."""
        program = await self.get_program_by_id(program_id)
        if not program:
            raise NotFoundException("Programme non trouvé")

        result = await self.db.execute(
            select(ProgramPartner).where(ProgramPartner.program_id == program_id)
        )
        return list(result.scalars().all())

    async def add_partner_to_program(
        self,
        program_id: str,
        partner_external_id: str,
        partnership_type: str | None = None,
    ) -> ProgramPartner:
        """
        Ajoute un partenaire à un programme.

        Args:
            program_id: ID du programme.
            partner_external_id: ID du partenaire.
            partnership_type: Type de partenariat.

        Returns:
            Partenariat créé.

        Raises:
            NotFoundException: Si le programme n'existe pas.
            ConflictException: Si le partenariat existe déjà.
        """
        program = await self.get_program_by_id(program_id)
        if not program:
            raise NotFoundException("Programme non trouvé")

        # Vérifier si le partenariat existe déjà
        result = await self.db.execute(
            select(ProgramPartner).where(
                ProgramPartner.program_id == program_id,
                ProgramPartner.partner_external_id == partner_external_id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Ce partenaire est déjà associé au programme")

        partner = ProgramPartner(
            program_id=program_id,
            partner_external_id=partner_external_id,
            partnership_type=partnership_type,
        )
        self.db.add(partner)
        await self.db.flush()
        return partner

    async def update_program_partner(
        self,
        program_id: str,
        partner_external_id: str,
        **kwargs,
    ) -> ProgramPartner:
        """Met à jour un partenariat."""
        result = await self.db.execute(
            select(ProgramPartner).where(
                ProgramPartner.program_id == program_id,
                ProgramPartner.partner_external_id == partner_external_id,
            )
        )
        partner = result.scalar_one_or_none()
        if not partner:
            raise NotFoundException("Partenariat non trouvé")

        await self.db.execute(
            update(ProgramPartner)
            .where(
                ProgramPartner.program_id == program_id,
                ProgramPartner.partner_external_id == partner_external_id,
            )
            .values(**kwargs)
        )
        await self.db.flush()

        result = await self.db.execute(
            select(ProgramPartner).where(
                ProgramPartner.program_id == program_id,
                ProgramPartner.partner_external_id == partner_external_id,
            )
        )
        return result.scalar_one()

    async def remove_partner_from_program(
        self, program_id: str, partner_external_id: str
    ) -> None:
        """
        Retire un partenaire d'un programme.

        Args:
            program_id: ID du programme.
            partner_external_id: ID du partenaire.

        Raises:
            NotFoundException: Si le partenariat n'existe pas.
        """
        result = await self.db.execute(
            select(ProgramPartner).where(
                ProgramPartner.program_id == program_id,
                ProgramPartner.partner_external_id == partner_external_id,
            )
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Partenariat non trouvé")

        await self.db.execute(
            delete(ProgramPartner).where(
                ProgramPartner.program_id == program_id,
                ProgramPartner.partner_external_id == partner_external_id,
            )
        )
        await self.db.flush()
