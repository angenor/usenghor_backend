#!/usr/bin/env python3
"""
Seed script : Editorial Values (Mission, Vision, Valeurs fondamentales)
======================================================================
Crée les données de référence pour les contenus éditoriaux de l'Université Senghor.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_editorial_values.py
"""

import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.editorial import (
    EditorialCategory,
    EditorialContent,
    EditorialValueType,
)


# ============================================================================
# CATÉGORIE
# ============================================================================

VALUES_CATEGORY = {
    "code": "values",
    "name": "Valeurs",
    "description": "Contenus de présentation de l'université : mission, vision, valeurs fondamentales",
}


# ============================================================================
# SECTIONS (Mission, Vision, Histoire, Mot du Recteur) - Format EditorJS
# ============================================================================

SECTIONS_DATA = [
    {
        "key": "mission",
        "description": "Notre Mission",
        "value_type": EditorialValueType.JSON,
        "value": json.dumps({
            "time": 1706000000000,
            "blocks": [
                {
                    "type": "paragraph",
                    "data": {
                        "text": "L'Université Senghor d'Alexandrie est un opérateur direct de la Francophonie. Elle a pour mission de former des cadres africains de haut niveau en management et développement."
                    }
                },
                {
                    "type": "paragraph",
                    "data": {
                        "text": "Créée en 1990 par le Sommet des chefs d'État et de gouvernement ayant le français en partage, l'Université Senghor poursuit trois objectifs majeurs :"
                    }
                },
                {
                    "type": "list",
                    "data": {
                        "style": "unordered",
                        "items": [
                            "<b>Former</b> des professionnels africains de haut niveau capables de contribuer au développement de leur pays",
                            "<b>Promouvoir</b> le dialogue des cultures et le rapprochement des peuples",
                            "<b>Développer</b> les échanges scientifiques et techniques entre les pays francophones"
                        ]
                    }
                },
                {
                    "type": "paragraph",
                    "data": {
                        "text": "Située au cœur d'Alexandrie, ville symbole de rencontre entre les civilisations, l'Université Senghor accueille chaque année des étudiants venus de toute l'Afrique francophone."
                    }
                }
            ],
            "version": "2.28.2"
        }, ensure_ascii=False),
    },
    {
        "key": "vision",
        "description": "Notre Vision",
        "value_type": EditorialValueType.JSON,
        "value": json.dumps({
            "time": 1706000000000,
            "blocks": [
                {
                    "type": "paragraph",
                    "data": {
                        "text": "L'Université Senghor aspire à devenir un <b>centre d'excellence reconnu internationalement</b> pour la formation des leaders africains du développement durable."
                    }
                },
                {
                    "type": "paragraph",
                    "data": {
                        "text": "Notre vision repose sur plusieurs piliers :"
                    }
                },
                {
                    "type": "list",
                    "data": {
                        "style": "unordered",
                        "items": [
                            "<b>Excellence académique</b> : Offrir des formations de qualité internationale répondant aux besoins du continent africain",
                            "<b>Innovation pédagogique</b> : Adopter des méthodes d'enseignement innovantes et adaptées aux défis contemporains",
                            "<b>Réseau d'influence</b> : Constituer un réseau d'anciens étudiants influents dans tous les secteurs clés du développement",
                            "<b>Partenariats stratégiques</b> : Développer des collaborations avec les meilleures institutions mondiales"
                        ]
                    }
                },
                {
                    "type": "paragraph",
                    "data": {
                        "text": "À l'horizon 2030, nous visons à avoir formé plus de 10 000 cadres africains contribuant activement au développement de leur pays."
                    }
                }
            ],
            "version": "2.28.2"
        }, ensure_ascii=False),
    },
    {
        "key": "history",
        "description": "Notre Histoire",
        "value_type": EditorialValueType.JSON,
        "value": json.dumps({
            "time": 1706000000000,
            "blocks": [
                {
                    "type": "paragraph",
                    "data": {
                        "text": "L'Université Senghor tire son nom de <b>Léopold Sédar Senghor</b> (1906-2001), poète, écrivain et homme d'État sénégalais, premier président de la République du Sénégal et ardent défenseur de la Francophonie."
                    }
                },
                {
                    "type": "header",
                    "data": {
                        "text": "Les dates clés",
                        "level": 3
                    }
                },
                {
                    "type": "list",
                    "data": {
                        "style": "unordered",
                        "items": [
                            "<b>1990</b> : Création de l'Université par le Sommet des chefs d'État et de gouvernement ayant le français en partage",
                            "<b>1992</b> : Accueil de la première promotion d'étudiants",
                            "<b>2000</b> : Lancement des premiers programmes de formation continue",
                            "<b>2010</b> : Inauguration du nouveau campus à Alexandrie",
                            "<b>2015</b> : Obtention de l'accréditation internationale",
                            "<b>2020</b> : Célébration des 30 ans avec plus de 5000 diplômés"
                        ]
                    }
                },
                {
                    "type": "paragraph",
                    "data": {
                        "text": "Depuis sa création, l'Université Senghor a formé des milliers de cadres africains qui occupent aujourd'hui des postes de responsabilité dans leurs pays respectifs et dans les organisations internationales."
                    }
                }
            ],
            "version": "2.28.2"
        }, ensure_ascii=False),
    },
    {
        "key": "rector_message",
        "description": "Mot du Recteur",
        "value_type": EditorialValueType.JSON,
        "value": json.dumps({
            "time": 1706000000000,
            "blocks": [
                {
                    "type": "paragraph",
                    "data": {
                        "text": "Chers étudiants, chers partenaires, chers amis de l'Université Senghor,"
                    }
                },
                {
                    "type": "paragraph",
                    "data": {
                        "text": "C'est avec une grande fierté que je vous accueille au sein de notre institution, <b>opérateur direct de la Francophonie</b> dédié à la formation des cadres africains de haut niveau."
                    }
                },
                {
                    "type": "paragraph",
                    "data": {
                        "text": "Depuis plus de trois décennies, l'Université Senghor s'est imposée comme un acteur incontournable de la coopération universitaire francophone. Notre ambition est claire : former les leaders de demain, capables de relever les défis du développement durable de l'Afrique."
                    }
                },
                {
                    "type": "paragraph",
                    "data": {
                        "text": "Notre approche pédagogique unique, combinant <b>excellence académique</b>, <b>expérience professionnelle</b> et <b>diversité culturelle</b>, permet à nos étudiants d'acquérir les compétences nécessaires pour transformer positivement leur environnement."
                    }
                },
                {
                    "type": "paragraph",
                    "data": {
                        "text": "Je vous invite à découvrir nos programmes de formation et à rejoindre notre communauté de plus de 5000 diplômés présents dans toute l'Afrique et au-delà."
                    }
                },
                {
                    "type": "paragraph",
                    "data": {
                        "text": "Bienvenue à l'Université Senghor !"
                    }
                },
                {
                    "type": "paragraph",
                    "data": {
                        "text": "<i>Professeur Jean-Dominique Pénel<br>Recteur de l'Université Senghor</i>"
                    }
                }
            ],
            "version": "2.28.2"
        }, ensure_ascii=False),
    },
]


# ============================================================================
# VALEURS FONDAMENTALES (Core Values)
# ============================================================================

CORE_VALUES_DATA = [
    {
        "title": "Excellence",
        "description": "Nous visons l'excellence dans l'enseignement, la recherche et le service à la communauté. Nos programmes sont conçus pour atteindre les plus hauts standards internationaux.",
        "icon": "star",
        "display_order": 1,
        "is_active": True,
    },
    {
        "title": "Intégrité",
        "description": "Nous agissons avec honnêteté, éthique et transparence dans toutes nos activités. L'intégrité est au cœur de notre engagement envers nos étudiants et partenaires.",
        "icon": "shield-alt",
        "display_order": 2,
        "is_active": True,
    },
    {
        "title": "Innovation",
        "description": "Nous encourageons la créativité, l'esprit d'entreprise et l'innovation pédagogique. Nous préparons nos étudiants à anticiper et à créer le changement.",
        "icon": "lightbulb",
        "display_order": 3,
        "is_active": True,
    },
    {
        "title": "Solidarité",
        "description": "Nous cultivons l'esprit de solidarité et d'entraide au sein de notre communauté universitaire et avec nos partenaires africains et internationaux.",
        "icon": "handshake",
        "display_order": 4,
        "is_active": True,
    },
    {
        "title": "Diversité",
        "description": "Nous célébrons la diversité culturelle et linguistique de nos étudiants venus de toute l'Afrique francophone. Cette richesse est notre force.",
        "icon": "globe",
        "display_order": 5,
        "is_active": True,
    },
    {
        "title": "Engagement",
        "description": "Nous formons des leaders engagés pour le développement durable de l'Afrique, conscients de leur responsabilité sociale et environnementale.",
        "icon": "seedling",
        "display_order": 6,
        "is_active": True,
    },
]


async def seed():
    """Insère les données de seed pour les contenus éditoriaux."""
    async with async_session_maker() as db:
        # Vérifier/créer la catégorie "values"
        existing_cat = (
            await db.execute(
                select(EditorialCategory).where(
                    EditorialCategory.code == VALUES_CATEGORY["code"]
                )
            )
        ).scalar_one_or_none()

        if existing_cat:
            category_id = existing_cat.id
            print(f"[INFO] Catégorie '{VALUES_CATEGORY['code']}' existe déjà (ID: {category_id})")
        else:
            category_id = str(uuid4())
            category = EditorialCategory(
                id=category_id,
                code=VALUES_CATEGORY["code"],
                name=VALUES_CATEGORY["name"],
                description=VALUES_CATEGORY["description"],
            )
            db.add(category)
            await db.flush()
            print(f"[OK] Catégorie '{VALUES_CATEGORY['code']}' créée (ID: {category_id})")

        # Vérifier si des contenus existent déjà pour cette catégorie
        existing_contents = (
            await db.execute(
                select(EditorialContent).where(
                    EditorialContent.category_id == category_id
                )
            )
        ).scalars().all()

        if existing_contents:
            print(f"[SKIP] {len(existing_contents)} contenus existent déjà. Seed ignoré.")
            print("       Utilisez 'python scripts/seed_editorial_values.py --force' pour recréer.")
            return

        sections_created = []
        core_values_created = []

        # Créer les sections
        for data in SECTIONS_DATA:
            content = EditorialContent(
                id=str(uuid4()),
                key=data["key"],
                value=data["value"],
                value_type=data["value_type"],
                category_id=category_id,
                description=data["description"],
                admin_editable=True,
            )
            db.add(content)
            sections_created.append(content)

        # Créer les valeurs fondamentales (stockées en JSON)
        for data in CORE_VALUES_DATA:
            key = f"core_value_{str(uuid4())[:8]}"
            content = EditorialContent(
                id=str(uuid4()),
                key=key,
                value=json.dumps(data, ensure_ascii=False),
                value_type=EditorialValueType.JSON,
                category_id=category_id,
                description=data["title"],
                admin_editable=True,
            )
            db.add(content)
            core_values_created.append(content)

        await db.commit()

        print()
        print("=" * 60)
        print("Seed des contenus éditoriaux terminé avec succès !")
        print("=" * 60)
        print(f"  Catégorie : {VALUES_CATEGORY['name']}")
        print(f"  Sections créées : {len(sections_created)}")
        for s in sections_created:
            print(f"    - {s.key}: {s.description}")
        print(f"  Valeurs fondamentales créées : {len(core_values_created)}")
        for v in core_values_created:
            print(f"    - {v.description}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
