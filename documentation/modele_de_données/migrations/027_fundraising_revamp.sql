-- ============================================================================
-- MIGRATION 027: Refonte Levée de Fonds (010-fundraising-revamp)
-- ============================================================================
-- Ajout: show_amount_publicly, fundraiser_interest_expressions,
--        fundraiser_editorial_sections, fundraiser_editorial_items,
--        fundraiser_media
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. ALTER fundraiser_contributors : ajout show_amount_publicly
-- ============================================================================

ALTER TABLE fundraiser_contributors
    ADD COLUMN IF NOT EXISTS show_amount_publicly BOOLEAN DEFAULT FALSE NOT NULL;

-- ============================================================================
-- 1b. ALTER fundraisers : ajout colonnes reason_* (contenu enrichi trilingue)
-- ============================================================================

ALTER TABLE fundraisers ADD COLUMN IF NOT EXISTS reason_html TEXT;
ALTER TABLE fundraisers ADD COLUMN IF NOT EXISTS reason_md TEXT;
ALTER TABLE fundraisers ADD COLUMN IF NOT EXISTS reason_en_html TEXT;
ALTER TABLE fundraisers ADD COLUMN IF NOT EXISTS reason_en_md TEXT;
ALTER TABLE fundraisers ADD COLUMN IF NOT EXISTS reason_ar_html TEXT;
ALTER TABLE fundraisers ADD COLUMN IF NOT EXISTS reason_ar_md TEXT;

-- ============================================================================
-- 2. TYPE ENUM : statut de suivi des manifestations d'intérêt
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE interest_expression_status AS ENUM ('new', 'contacted');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================================
-- 3. CREATE fundraiser_interest_expressions
-- ============================================================================

CREATE TABLE IF NOT EXISTS fundraiser_interest_expressions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fundraiser_id UUID NOT NULL REFERENCES fundraisers(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    message TEXT,
    status interest_expression_status DEFAULT 'new' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT uq_interest_email_fundraiser UNIQUE (email, fundraiser_id)
);

CREATE INDEX IF NOT EXISTS idx_interest_expressions_fundraiser_id
    ON fundraiser_interest_expressions(fundraiser_id);
CREATE INDEX IF NOT EXISTS idx_interest_expressions_status
    ON fundraiser_interest_expressions(status);

CREATE TRIGGER update_interest_expressions_updated_at
    BEFORE UPDATE ON fundraiser_interest_expressions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 4. CREATE fundraiser_editorial_sections
-- ============================================================================

CREATE TABLE IF NOT EXISTS fundraiser_editorial_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(100) UNIQUE NOT NULL,
    title_fr VARCHAR(255) NOT NULL,
    title_en VARCHAR(255),
    title_ar VARCHAR(255),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TRIGGER update_editorial_sections_updated_at
    BEFORE UPDATE ON fundraiser_editorial_sections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 5. CREATE fundraiser_editorial_items
-- ============================================================================

CREATE TABLE IF NOT EXISTS fundraiser_editorial_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section_id UUID NOT NULL REFERENCES fundraiser_editorial_sections(id) ON DELETE CASCADE,
    icon VARCHAR(100) NOT NULL,
    title_fr VARCHAR(255) NOT NULL,
    title_en VARCHAR(255),
    title_ar VARCHAR(255),
    description_fr TEXT NOT NULL,
    description_en TEXT,
    description_ar TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_editorial_items_section_id
    ON fundraiser_editorial_items(section_id);

CREATE TRIGGER update_editorial_items_updated_at
    BEFORE UPDATE ON fundraiser_editorial_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. CREATE fundraiser_media
-- ============================================================================

CREATE TABLE IF NOT EXISTS fundraiser_media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fundraiser_id UUID NOT NULL REFERENCES fundraisers(id) ON DELETE CASCADE,
    media_external_id UUID NOT NULL,
    caption_fr VARCHAR(500),
    caption_en VARCHAR(500),
    caption_ar VARCHAR(500),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT uq_fundraiser_media UNIQUE (fundraiser_id, media_external_id)
);

CREATE INDEX IF NOT EXISTS idx_fundraiser_media_fundraiser_id
    ON fundraiser_media(fundraiser_id);

-- ============================================================================
-- 7. SEED : 3 sections éditoriales avec items d'exemple
-- ============================================================================

-- Section 1 : Votre contribution sert à
INSERT INTO fundraiser_editorial_sections (id, slug, title_fr, title_en, title_ar, display_order, is_active)
VALUES (
    uuid_generate_v4(),
    'contribution-reasons',
    'Votre contribution sert à',
    'Your contribution is used for',
    'مساهمتكم تخدم',
    0,
    TRUE
);

-- Section 2 : Exemples d'engagement
INSERT INTO fundraiser_editorial_sections (id, slug, title_fr, title_en, title_ar, display_order, is_active)
VALUES (
    uuid_generate_v4(),
    'engagement-examples',
    'Exemples d''engagement',
    'Examples of commitment',
    'أمثلة على الالتزام',
    1,
    TRUE
);

-- Section 3 : Bénéfices liés à votre contribution
INSERT INTO fundraiser_editorial_sections (id, slug, title_fr, title_en, title_ar, display_order, is_active)
VALUES (
    uuid_generate_v4(),
    'contribution-benefits',
    'Bénéfices liés à votre contribution',
    'Benefits of your contribution',
    'فوائد مساهمتكم',
    2,
    TRUE
);

-- Items d'exemple pour Section 1 (contribution-reasons)
INSERT INTO fundraiser_editorial_items (id, section_id, icon, title_fr, title_en, title_ar, description_fr, description_en, description_ar, display_order, is_active)
SELECT
    uuid_generate_v4(),
    s.id,
    'academic-cap',
    'Former les leaders de demain',
    'Training tomorrow''s leaders',
    'تدريب قادة الغد',
    'Votre soutien finance des bourses d''études pour des étudiants méritants venus de toute l''Afrique et de la Francophonie.',
    'Your support funds scholarships for deserving students from across Africa and the Francophonie.',
    'يموّل دعمكم منحاً دراسية لطلاب مستحقين من أنحاء أفريقيا والفرنكوفونية.',
    0,
    TRUE
FROM fundraiser_editorial_sections s WHERE s.slug = 'contribution-reasons';

INSERT INTO fundraiser_editorial_items (id, section_id, icon, title_fr, title_en, title_ar, description_fr, description_en, description_ar, display_order, is_active)
SELECT
    uuid_generate_v4(),
    s.id,
    'building-library',
    'Moderniser les infrastructures',
    'Modernizing infrastructure',
    'تحديث البنية التحتية',
    'Contribuez à la rénovation et l''équipement des campus pour offrir un environnement d''apprentissage de qualité.',
    'Contribute to the renovation and equipping of campuses to provide a quality learning environment.',
    'ساهموا في تجديد وتجهيز الحرم الجامعي لتوفير بيئة تعليمية ذات جودة.',
    1,
    TRUE
FROM fundraiser_editorial_sections s WHERE s.slug = 'contribution-reasons';

INSERT INTO fundraiser_editorial_items (id, section_id, icon, title_fr, title_en, title_ar, description_fr, description_en, description_ar, display_order, is_active)
SELECT
    uuid_generate_v4(),
    s.id,
    'globe-alt',
    'Renforcer la coopération internationale',
    'Strengthening international cooperation',
    'تعزيز التعاون الدولي',
    'Participez au développement de partenariats académiques et de programmes d''échange à travers le monde.',
    'Participate in the development of academic partnerships and exchange programs around the world.',
    'شاركوا في تطوير الشراكات الأكاديمية وبرامج التبادل حول العالم.',
    2,
    TRUE
FROM fundraiser_editorial_sections s WHERE s.slug = 'contribution-reasons';

-- Items d'exemple pour Section 2 (engagement-examples)
INSERT INTO fundraiser_editorial_items (id, section_id, icon, title_fr, title_en, title_ar, description_fr, description_en, description_ar, display_order, is_active)
SELECT
    uuid_generate_v4(),
    s.id,
    'currency-euro',
    'Don financier',
    'Financial donation',
    'تبرع مالي',
    'Effectuez un don unique ou récurrent pour soutenir les activités de l''université.',
    'Make a one-time or recurring donation to support the university''s activities.',
    'قدّموا تبرعاً لمرة واحدة أو متكرراً لدعم أنشطة الجامعة.',
    0,
    TRUE
FROM fundraiser_editorial_sections s WHERE s.slug = 'engagement-examples';

INSERT INTO fundraiser_editorial_items (id, section_id, icon, title_fr, title_en, title_ar, description_fr, description_en, description_ar, display_order, is_active)
SELECT
    uuid_generate_v4(),
    s.id,
    'users',
    'Parrainage d''étudiants',
    'Student sponsorship',
    'رعاية الطلاب',
    'Parrainez un ou plusieurs étudiants en finançant leur parcours académique complet.',
    'Sponsor one or more students by funding their complete academic journey.',
    'اكفلوا طالباً أو أكثر بتمويل مسيرتهم الأكاديمية الكاملة.',
    1,
    TRUE
FROM fundraiser_editorial_sections s WHERE s.slug = 'engagement-examples';

INSERT INTO fundraiser_editorial_items (id, section_id, icon, title_fr, title_en, title_ar, description_fr, description_en, description_ar, display_order, is_active)
SELECT
    uuid_generate_v4(),
    s.id,
    'briefcase',
    'Partenariat institutionnel',
    'Institutional partnership',
    'شراكة مؤسسية',
    'Établissez un partenariat stratégique avec l''université pour des projets de recherche ou de formation.',
    'Establish a strategic partnership with the university for research or training projects.',
    'أنشئوا شراكة استراتيجية مع الجامعة لمشاريع البحث أو التكوين.',
    2,
    TRUE
FROM fundraiser_editorial_sections s WHERE s.slug = 'engagement-examples';

-- Items d'exemple pour Section 3 (contribution-benefits)
INSERT INTO fundraiser_editorial_items (id, section_id, icon, title_fr, title_en, title_ar, description_fr, description_en, description_ar, display_order, is_active)
SELECT
    uuid_generate_v4(),
    s.id,
    'shield-check',
    'Visibilité et reconnaissance',
    'Visibility and recognition',
    'الرؤية والاعتراف',
    'Bénéficiez d''une visibilité sur nos supports de communication et lors de nos événements.',
    'Benefit from visibility on our communication materials and at our events.',
    'استفيدوا من الظهور على مواد التواصل الخاصة بنا وفي فعالياتنا.',
    0,
    TRUE
FROM fundraiser_editorial_sections s WHERE s.slug = 'contribution-benefits';

INSERT INTO fundraiser_editorial_items (id, section_id, icon, title_fr, title_en, title_ar, description_fr, description_en, description_ar, display_order, is_active)
SELECT
    uuid_generate_v4(),
    s.id,
    'document-text',
    'Avantages fiscaux',
    'Tax benefits',
    'مزايا ضريبية',
    'Profitez de déductions fiscales conformément à la législation en vigueur dans votre pays.',
    'Take advantage of tax deductions in accordance with the legislation in your country.',
    'استفيدوا من الخصومات الضريبية وفقاً للتشريعات المعمول بها في بلدكم.',
    1,
    TRUE
FROM fundraiser_editorial_sections s WHERE s.slug = 'contribution-benefits';

INSERT INTO fundraiser_editorial_items (id, section_id, icon, title_fr, title_en, title_ar, description_fr, description_en, description_ar, display_order, is_active)
SELECT
    uuid_generate_v4(),
    s.id,
    'chart-bar',
    'Rapports d''impact',
    'Impact reports',
    'تقارير الأثر',
    'Recevez des rapports réguliers sur l''utilisation de vos contributions et l''impact généré.',
    'Receive regular reports on the use of your contributions and the impact generated.',
    'احصلوا على تقارير منتظمة حول استخدام مساهماتكم والأثر المحقق.',
    2,
    TRUE
FROM fundraiser_editorial_sections s WHERE s.slug = 'contribution-benefits';

COMMIT;

-- ============================================================================
-- FIN DE LA MIGRATION 027
-- ============================================================================
