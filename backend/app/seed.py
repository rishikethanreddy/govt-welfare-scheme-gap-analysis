"""
Seed data script — populates the database with initial reference data.

- 15 government welfare schemes
- India states and union territories
- Initial CSV dataset import

Run: python -m backend.app.seed
"""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.database import SessionLocal, Base, engine
from backend.app.models.scheme import Scheme
from backend.app.models.geography import GeographicEntity
from backend.app.models.source import Source
from backend.app.models.audit import AuditLog
from backend.app.services.dataset import DatasetService


# ── Scheme Data ───────────────────────────────────────────────────────────

SCHEMES = [
    {
        "name": "Pradhan Mantri Kisan Samman Nidhi",
        "short_name": "PM-KISAN",
        "category": "agriculture",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "aliases": "pm kisan,pm-kisan,pmkisan,kisan samman nidhi,pradhan mantri kisan",
        "official_url": "https://pmkisan.gov.in/",
        "display_order": 1,
    },
    {
        "name": "Pradhan Mantri Fasal Bima Yojana",
        "short_name": "PMFBY",
        "category": "agriculture",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "aliases": "pmfby,fasal bima,crop insurance,pradhan mantri fasal bima yojana",
        "official_url": "https://pmfby.gov.in/",
        "display_order": 2,
    },
    {
        "name": "Pradhan Mantri Kisan Urja Suraksha evam Utthaan Mahabhiyan",
        "short_name": "PM-KUSUM",
        "category": "energy",
        "ministry": "Ministry of New and Renewable Energy",
        "aliases": "pm kusum,pm-kusum,solar pump,kusum yojana",
        "official_url": "https://mnre.gov.in/",
        "display_order": 3,
    },
    {
        "name": "Pradhan Mantri Awas Yojana",
        "short_name": "PMAY",
        "category": "housing",
        "ministry": "Ministry of Housing and Urban Affairs",
        "aliases": "pmay,awas yojana,pm awas,housing scheme,pradhan mantri awas yojana",
        "official_url": "https://pmaymis.gov.in/",
        "display_order": 4,
    },
    {
        "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana",
        "short_name": "Ayushman Bharat PM-JAY",
        "category": "health",
        "ministry": "Ministry of Health and Family Welfare",
        "aliases": "ayushman bharat,pm-jay,pmjay,ayushman card,health card",
        "official_url": "https://pmjay.gov.in/",
        "display_order": 5,
    },
    {
        "name": "Mahatma Gandhi National Rural Employment Guarantee Act",
        "short_name": "MGNREGA",
        "category": "employment",
        "ministry": "Ministry of Rural Development",
        "aliases": "mgnrega,nrega,100 days work,job card,mahatma gandhi nrega",
        "official_url": "https://nrega.nic.in/",
        "display_order": 6,
    },
    {
        "name": "Pradhan Mantri Jan Dhan Yojana",
        "short_name": "PMJDY",
        "category": "financial",
        "ministry": "Ministry of Finance",
        "aliases": "pmjdy,jan dhan,zero balance account",
        "official_url": "https://pmjdy.gov.in/",
        "display_order": 7,
    },
    {
        "name": "Pradhan Mantri Mudra Yojana",
        "short_name": "PMMY",
        "category": "financial",
        "ministry": "Ministry of Finance",
        "aliases": "pmmy,mudra yojana,mudra loan,shishu loan,tarun loan,kishore loan",
        "official_url": "https://www.mudra.org.in/",
        "display_order": 8,
    },
    {
        "name": "PM Street Vendor's AtmaNirbhar Nidhi",
        "short_name": "PM SVANidhi",
        "category": "financial",
        "ministry": "Ministry of Housing and Urban Affairs",
        "aliases": "svanidhi,street vendor,pm svanidhi",
        "official_url": "https://pmsvanidhi.mohua.gov.in/",
        "display_order": 9,
    },
    {
        "name": "Atal Pension Yojana",
        "short_name": "APY",
        "category": "insurance",
        "ministry": "Ministry of Finance",
        "aliases": "apy,atal pension",
        "official_url": "https://www.npscra.nsdl.co.in/",
        "display_order": 10,
    },
    {
        "name": "Pradhan Mantri Jeevan Jyoti Bima Yojana",
        "short_name": "PMJJBY",
        "category": "insurance",
        "ministry": "Ministry of Finance",
        "aliases": "pmjjby,jeevan jyoti",
        "display_order": 11,
    },
    {
        "name": "Pradhan Mantri Suraksha Bima Yojana",
        "short_name": "PMSBY",
        "category": "insurance",
        "ministry": "Ministry of Finance",
        "aliases": "pmsby,suraksha bima",
        "display_order": 12,
    },
    {
        "name": "National Social Assistance Programme",
        "short_name": "NSAP",
        "category": "social",
        "ministry": "Ministry of Rural Development",
        "aliases": "nsap,old age pension,widow pension,disability pension",
        "display_order": 13,
    },
    {
        "name": "Pradhan Mantri Ujjwala Yojana",
        "short_name": "PMUY",
        "category": "energy",
        "ministry": "Ministry of Petroleum and Natural Gas",
        "aliases": "pmuy,ujjwala,gas cylinder scheme,free gas",
        "official_url": "https://www.pmuy.gov.in/",
        "display_order": 14,
    },
    {
        "name": "PM Vishwakarma",
        "short_name": "PM Vishwakarma",
        "category": "employment",
        "ministry": "Ministry of Micro, Small and Medium Enterprises",
        "aliases": "vishwakarma,artisan scheme,pm vishwakarma",
        "official_url": "https://pmvishwakarma.gov.in/",
        "display_order": 15,
    },
]


# ── India States & UTs ───────────────────────────────────────────────────

STATES = [
    {"name": "Andhra Pradesh", "code": "AP", "iso_code": "IN-AP", "entity_type": "state", "latitude": 15.9129, "longitude": 79.7400},
    {"name": "Arunachal Pradesh", "code": "AR", "iso_code": "IN-AR", "entity_type": "state", "latitude": 28.2180, "longitude": 94.7278},
    {"name": "Assam", "code": "AS", "iso_code": "IN-AS", "entity_type": "state", "latitude": 26.2006, "longitude": 92.9376},
    {"name": "Bihar", "code": "BR", "iso_code": "IN-BR", "entity_type": "state", "latitude": 25.0961, "longitude": 85.3131},
    {"name": "Chhattisgarh", "code": "CT", "iso_code": "IN-CT", "entity_type": "state", "latitude": 21.2787, "longitude": 81.8661},
    {"name": "Goa", "code": "GA", "iso_code": "IN-GA", "entity_type": "state", "latitude": 15.2993, "longitude": 74.1240},
    {"name": "Gujarat", "code": "GJ", "iso_code": "IN-GJ", "entity_type": "state", "latitude": 22.2587, "longitude": 71.1924},
    {"name": "Haryana", "code": "HR", "iso_code": "IN-HR", "entity_type": "state", "latitude": 29.0588, "longitude": 76.0856},
    {"name": "Himachal Pradesh", "code": "HP", "iso_code": "IN-HP", "entity_type": "state", "latitude": 31.1048, "longitude": 77.1734},
    {"name": "Jharkhand", "code": "JH", "iso_code": "IN-JH", "entity_type": "state", "latitude": 23.6102, "longitude": 85.2799},
    {"name": "Karnataka", "code": "KA", "iso_code": "IN-KA", "entity_type": "state", "latitude": 15.3173, "longitude": 75.7139},
    {"name": "Kerala", "code": "KL", "iso_code": "IN-KL", "entity_type": "state", "latitude": 10.8505, "longitude": 76.2711},
    {"name": "Madhya Pradesh", "code": "MP", "iso_code": "IN-MP", "entity_type": "state", "latitude": 22.9734, "longitude": 78.6569},
    {"name": "Maharashtra", "code": "MH", "iso_code": "IN-MH", "entity_type": "state", "latitude": 19.7515, "longitude": 75.7139},
    {"name": "Manipur", "code": "MN", "iso_code": "IN-MN", "entity_type": "state", "latitude": 24.6637, "longitude": 93.9063},
    {"name": "Meghalaya", "code": "ML", "iso_code": "IN-ML", "entity_type": "state", "latitude": 25.4670, "longitude": 91.3662},
    {"name": "Mizoram", "code": "MZ", "iso_code": "IN-MZ", "entity_type": "state", "latitude": 23.1645, "longitude": 92.9376},
    {"name": "Nagaland", "code": "NL", "iso_code": "IN-NL", "entity_type": "state", "latitude": 26.1584, "longitude": 94.5624},
    {"name": "Odisha", "code": "OR", "iso_code": "IN-OR", "entity_type": "state", "latitude": 20.9517, "longitude": 85.0985},
    {"name": "Punjab", "code": "PB", "iso_code": "IN-PB", "entity_type": "state", "latitude": 31.1471, "longitude": 75.3412},
    {"name": "Rajasthan", "code": "RJ", "iso_code": "IN-RJ", "entity_type": "state", "latitude": 27.0238, "longitude": 74.2179},
    {"name": "Sikkim", "code": "SK", "iso_code": "IN-SK", "entity_type": "state", "latitude": 27.5330, "longitude": 88.5122},
    {"name": "Tamil Nadu", "code": "TN", "iso_code": "IN-TN", "entity_type": "state", "latitude": 11.1271, "longitude": 78.6569},
    {"name": "Telangana", "code": "TG", "iso_code": "IN-TG", "entity_type": "state", "latitude": 18.1124, "longitude": 79.0193},
    {"name": "Tripura", "code": "TR", "iso_code": "IN-TR", "entity_type": "state", "latitude": 23.9408, "longitude": 91.9882},
    {"name": "Uttar Pradesh", "code": "UP", "iso_code": "IN-UP", "entity_type": "state", "latitude": 26.8467, "longitude": 80.9462},
    {"name": "Uttarakhand", "code": "UK", "iso_code": "IN-UK", "entity_type": "state", "latitude": 30.0668, "longitude": 79.0193},
    {"name": "West Bengal", "code": "WB", "iso_code": "IN-WB", "entity_type": "state", "latitude": 22.9868, "longitude": 87.8550},
    # Union Territories
    {"name": "Andaman and Nicobar Islands", "code": "AN", "iso_code": "IN-AN", "entity_type": "union_territory", "latitude": 11.7401, "longitude": 92.6586},
    {"name": "Chandigarh", "code": "CH", "iso_code": "IN-CH", "entity_type": "union_territory", "latitude": 30.7333, "longitude": 76.7794},
    {"name": "Dadra and Nagar Haveli and Daman and Diu", "code": "DD", "iso_code": "IN-DD", "entity_type": "union_territory", "latitude": 20.1809, "longitude": 73.0169},
    {"name": "Delhi", "code": "DL", "iso_code": "IN-DL", "entity_type": "union_territory", "latitude": 28.7041, "longitude": 77.1025},
    {"name": "Jammu and Kashmir", "code": "JK", "iso_code": "IN-JK", "entity_type": "union_territory", "latitude": 33.7782, "longitude": 76.5762},
    {"name": "Ladakh", "code": "LA", "iso_code": "IN-LA", "entity_type": "union_territory", "latitude": 34.1526, "longitude": 77.5771},
    {"name": "Lakshadweep", "code": "LD", "iso_code": "IN-LD", "entity_type": "union_territory", "latitude": 10.5667, "longitude": 72.6417},
    {"name": "Puducherry", "code": "PY", "iso_code": "IN-PY", "entity_type": "union_territory", "latitude": 11.9416, "longitude": 79.8083},
]


def seed_schemes(db):
    """Seed the 15 welfare schemes."""
    existing = db.query(Scheme).count()
    if existing > 0:
        print(f"  Schemes already seeded ({existing} found). Skipping.")
        return

    for s in SCHEMES:
        scheme = Scheme(**s, active=True)
        db.add(scheme)

    db.commit()
    print(f"  [OK] Seeded {len(SCHEMES)} welfare schemes")


def seed_geography(db):
    """Seed India states and union territories."""
    existing = db.query(GeographicEntity).count()
    if existing > 0:
        print(f"  Geography already seeded ({existing} found). Skipping.")
        return

    # Add India
    india = GeographicEntity(
        name="India", entity_type="country", code="IN",
        iso_code="IN", latitude=20.5937, longitude=78.9629,
    )
    db.add(india)
    db.flush()

    for s in STATES:
        state = GeographicEntity(parent_id=india.id, **s)
        db.add(state)

    db.commit()
    print(f"  [OK] Seeded {len(STATES)} states/UTs + India")


def seed_initial_source(db):
    """Register the initial CSV dataset as a source."""
    existing = db.query(Source).filter(Source.name == "Initial CSV Dataset").first()
    if existing:
        print("  Initial source already exists. Skipping.")
        return

    source = Source(
        name="Initial CSV Dataset",
        source_type="csv_upload",
        organization="Research Project",
        description="Initial labeled dataset with 127 records across 15 welfare schemes",
        collection_method="manual",
        policy_status="allowed",
        active=True,
    )
    db.add(source)
    db.commit()
    print("  [OK] Registered initial CSV source")


def seed_dataset(db):
    """Import the initial CSV dataset if it exists."""
    csv_path = os.path.join("data", "raw", "welfare_awareness_dataset_with_split.csv")
    if not os.path.exists(csv_path):
        print(f"  CSV not found at {csv_path}. Skipping dataset import.")
        return

    svc = DatasetService(db)

    # Check if already imported
    from backend.app.models.processing import DatasetVersion
    existing = db.query(DatasetVersion).filter(DatasetVersion.version == "v1.0").first()
    if existing:
        print(f"  Dataset v1.0 already imported ({existing.record_count} records). Skipping.")
        return

    result = svc.ingest_csv(csv_path, version="v1.0", name="Initial Research Dataset")
    print(f"  [OK] Imported dataset v1.0: {result['valid_records']} records "
          f"({result['duplicate_records']} duplicates, {result['rejected_records']} rejected)")


def main():
    """Run all seed operations."""
    print("=" * 60)
    print("  Seeding Database")
    print("=" * 60)

    # Create tables
    Base.metadata.create_all(bind=engine)
    print("  [OK] Database tables created/verified")

    db = SessionLocal()
    try:
        seed_schemes(db)
        seed_geography(db)
        seed_initial_source(db)
        seed_dataset(db)

        # Audit log
        audit = AuditLog(
            action="system",
            description="Database seeded with initial reference data and dataset",
            severity="info",
        )
        db.add(audit)
        db.commit()

        print("=" * 60)
        print("  [OK] Seed complete!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"  [ERROR] Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
