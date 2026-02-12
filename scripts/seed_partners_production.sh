#!/bin/bash
# ==============================================================================
# Seed des partenaires en production
# ==============================================================================
# Télécharge les logos dans le volume Docker et insère les données en base.
#
# Usage (depuis la machine locale) :
#   ssh ubuntu@137.74.117.231 'bash -s' < usenghor_backend/scripts/seed_partners_production.sh
# ==============================================================================

set -euo pipefail

CONTAINER_BACKEND="usenghor_backend"
CONTAINER_DB="usenghor_db"
DB_USER="usenghor"
DB_NAME="usenghor"
LOGOS_DIR="/var/www/uploads/partners/logos"

echo "============================================================"
echo " Seed des partenaires — Production"
echo "============================================================"

# Créer le dossier logos dans le volume via le container backend
echo "[1/3] Création du dossier logos..."
docker exec "$CONTAINER_BACKEND" mkdir -p "$LOGOS_DIR"

# Données des partenaires : nom|website|logo_url
PARTNERS=(
  "OIF|https://www.francophonie.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/01.jpg"
  "APF|https://apf-francophonie.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/02.png"
  "AUF|https://www.auf.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/03.png"
  "AIMF|https://www.aimf.asso.fr/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/04.jpg"
  "Enap Quebec|https://enap.ca/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/1.png"
  "Université du Luxembourg|https://www.uni.lu/fr/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/2.png"
  "Université de Porto|https://www.up.pt/portal/en/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/3.png"
  "Institut français Égypte|https://www.ifegypte.com/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/5.png"
  "IBDL|https://ibdl.net/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/6.png"
  "Ina|https://www.ina.fr/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/7.png"
  "ICHEC|https://www.ichec.be/fr|https://usenghor-francophonie.org/wp-content/uploads/2023/09/8.png"
  "CEAlex|https://www.cealex.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/9.png"
  "Ramsar|https://www.ramsar.org/fr|https://usenghor-francophonie.org/wp-content/uploads/2023/09/10.png"
  "IUCN|https://www.iucn.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/11.png"
  "Sciences Po|https://www.sciencespo.fr/fr/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/12.png"
  "Rennes School Business|https://www.rennes-sb.fr/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/13.png"
  "Em Lyon Business School|https://em-lyon.com/en|https://usenghor-francophonie.org/wp-content/uploads/2023/09/14.png"
  "Enssib|https://www.enssib.fr/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/15.png"
  "CEAlex (CNRS)|https://www.cealex.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/16.png"
  "CMA|https://www.cmatlv.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/17.png"
  "UCAC|https://ucac-icy.net/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/18.png"
  "Université Catholique du Congo|https://ucc.ac.cd/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/19.jpg"
  "Université Szeged|https://u-szeged.hu/english|https://usenghor-francophonie.org/wp-content/uploads/2023/09/20.png"
  "Université Mohammed premier de Oujda|http://www.ump.ma/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/21.png"
  "Institut Français d'Archéologie Orientale|https://www.ifao.egnet.net/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/22.gif"
  "CAMES|https://www.lecames.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/24.jpg"
  "Make Sense Africa|https://makesense.org/en/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/25.png"
  "Université de Ouagadougou 2|https://www.univ-ouaga2.gov.bf/accueil|https://usenghor-francophonie.org/wp-content/uploads/2023/09/26.jpg"
  "École Nationale d'Administration (RDC)|https://ena.cd/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/27.png"
  "Institut Francophone International|https://ifi.vnu.edu.vn/fr/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/28-300x99.png"
  "IDG Dakar|https://www.idgdakar.com/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/29.png"
  "Trace|https://fr.trace.tv/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/31.jpg"
  "EAMAU|https://www.eamau.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/32.png"
  "CCI Côte d'Ivoire|https://www.cci.ci/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/33.jpg"
  "Université Gamal Abdel Nasser de Conakry|https://uganc.edu.gn/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/34.jpg"
  "Université de Parakou|http://www.univ-parakou.bj/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/35.png"
  "CCCPA|https://www.cccpa-eg.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/36.jpg"
  "Université de Pharos|https://www.pua.edu.eg/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/37.png"
  "Ministère égyptien des affaires étrangères|https://www.mfa.gov.eg/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/38.png"
  "IPMD|https://ipmd.pro/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/40.png"
  "ISCAM|https://www.iscam.mg/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/41.png"
  "Institut Supérieur Madiba|https://www.groupeism.sn/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/42.jpg"
  "Bioforce|https://www.bioforce.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/43.png"
  "Enaref|http://ena.enaref.gov.bf/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/44.jpg"
  "UGLC-SC|https://uglcs.org/home/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/45.png"
  "Institut National d'Assainissement et d'Urbanisme|https://inau.ac.ma/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/46.png"
  "Université d'Abomey Calavi|https://uac.bj/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/47.jpg"
  "Ista Cemac|https://www.ista-cemac.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/48.png"
  "CNFTPA|https://cnftpa.sn/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/49.png"
  "Imdr|https://www.imdr.eu/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/50.jpg"
  "Codatu|https://www.codatu.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/51.jpg"
  "Université Internationale de la Mer|https://www.univ-mer.org/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/52.png"
  "EABA||https://usenghor-francophonie.org/wp-content/uploads/2023/09/53.jpg"
  "FAO|https://www.fao.org/home/fr|https://usenghor-francophonie.org/wp-content/uploads/2023/09/54.png"
  "Unesco|https://www.unesco.org/fr|https://usenghor-francophonie.org/wp-content/uploads/2023/09/55.png"
  "École nationale des chartes|https://www.chartes.psl.eu/|https://usenghor-francophonie.org/wp-content/uploads/2023/09/4.png"
)

# Construire le SQL dynamiquement
echo "[2/3] Téléchargement des logos et génération du SQL..."

SQL_FILE=$(mktemp /tmp/seed_partners_XXXX.sql)
cat > "$SQL_FILE" <<'HEADER'
BEGIN;
HEADER

created=0
skipped=0
order=0

for entry in "${PARTNERS[@]}"; do
  IFS='|' read -r name website logo_url <<< "$entry"
  order=$((order + 1))

  # Vérifier si le partenaire existe déjà
  exists=$(docker exec "$CONTAINER_DB" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT COUNT(*) FROM partners WHERE name = '$(echo "$name" | sed "s/'/''/g")';" 2>/dev/null)

  if [ "$exists" -gt 0 ]; then
    echo "  [$order/56] $name — déjà en base, ignoré"
    skipped=$((skipped + 1))
    continue
  fi

  echo -n "  [$order/56] $name... "

  # Générer les UUID
  media_uuid=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen || python3 -c "import uuid; print(uuid.uuid4())")
  partner_uuid=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen || python3 -c "import uuid; print(uuid.uuid4())")

  # Nom de fichier sûr
  safe_name=$(echo "$name" | tr '[:upper:]' '[:lower:]' | sed "s/[^a-z0-9]/_/g" | sed "s/__*/_/g" | sed "s/^_//;s/_$//" | cut -c1-50)
  timestamp=$(date -u +%Y%m%d_%H%M%S)
  uid=$(echo "$media_uuid" | cut -c1-8)

  # Extension du fichier
  ext="${logo_url##*.}"
  case "$ext" in
    jpg|jpeg) ext="jpg"; mime="image/jpeg" ;;
    png) ext="png"; mime="image/png" ;;
    gif) ext="gif"; mime="image/gif" ;;
    *) ext="png"; mime="image/png" ;;
  esac

  filename="${timestamp}_${safe_name}_${uid}.${ext}"
  filepath="${LOGOS_DIR}/${filename}"
  relative_url="/uploads/partners/logos/${filename}"

  # Télécharger le logo dans le container backend
  docker exec "$CONTAINER_BACKEND" sh -c \
    "wget -q -O '${filepath}' '${logo_url}' 2>/dev/null || curl -sL -o '${filepath}' '${logo_url}'" 2>/dev/null

  # Vérifier si le fichier existe et a une taille > 0
  file_size=$(docker exec "$CONTAINER_BACKEND" sh -c "stat -c%s '${filepath}' 2>/dev/null || stat -f%z '${filepath}' 2>/dev/null || echo 0")

  if [ "$file_size" -gt 0 ] 2>/dev/null; then
    # Échapper les apostrophes pour SQL
    escaped_name=$(echo "$name" | sed "s/'/''/g")
    escaped_website=$(echo "$website" | sed "s/'/''/g")

    # SQL : Insérer le media
    cat >> "$SQL_FILE" <<EOSQL

-- ${name}
INSERT INTO media (id, name, type, url, is_external_url, size_bytes, mime_type, alt_text)
VALUES ('${media_uuid}', 'Logo ${escaped_name}', 'image'::media_type, '${relative_url}', FALSE, ${file_size}, '${mime}', 'Logo du partenaire ${escaped_name}');

INSERT INTO partners (id, name, logo_external_id, website, type, active, display_order)
VALUES ('${partner_uuid}', '${escaped_name}', '${media_uuid}', $([ -n "$website" ] && echo "'${escaped_website}'" || echo "NULL"), 'campus_partner'::partner_type, TRUE, ${order});
EOSQL

    echo "OK (avec logo, ${file_size} octets)"
    created=$((created + 1))
  else
    # Sans logo
    escaped_name=$(echo "$name" | sed "s/'/''/g")
    escaped_website=$(echo "$website" | sed "s/'/''/g")

    cat >> "$SQL_FILE" <<EOSQL

-- ${name} (sans logo)
INSERT INTO partners (id, name, website, type, active, display_order)
VALUES ('${partner_uuid}', '${escaped_name}', $([ -n "$website" ] && echo "'${escaped_website}'" || echo "NULL"), 'campus_partner'::partner_type, TRUE, ${order});
EOSQL

    echo "OK (sans logo)"
    created=$((created + 1))
  fi
done

echo "COMMIT;" >> "$SQL_FILE"

# Exécuter le SQL
echo ""
echo "[3/3] Insertion en base de données..."
docker exec -i "$CONTAINER_DB" psql -U "$DB_USER" -d "$DB_NAME" < "$SQL_FILE"

# Nettoyage
rm -f "$SQL_FILE"

echo ""
echo "============================================================"
echo "  Créés   : $created"
echo "  Ignorés : $skipped (déjà en base)"
echo "============================================================"
echo "[OK] Seed production terminé"
