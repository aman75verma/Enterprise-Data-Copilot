"""
Enterprise Data Copilot — Seed Script (SaaS/BaaS Model)
Generates realistic story-driven synthetic data for the Supabase-like schema.

Usage:
    python seed.py

Requires:
    pip install faker psycopg2-binary python-dotenv
"""

import os
import random
import uuid
import string
from datetime import datetime, timedelta
from decimal import Decimal

import psycopg2
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from faker import Faker

load_dotenv()

fake = Faker()
Faker.seed(42)  # Reproducible data
random.seed(42)

# ---------------------------------------------------------
# Database connection
# ---------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://copilot:copilot_pass@localhost:5433/copilot_db"
)


def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
NUM_CUSTOMERS = 50
NUM_ORGS = 40
NUM_PROJECTS = 80
NUM_AGENTS = 5

PLANS = ["free", "pro", "team", "enterprise"]
PLAN_MRR = {
    "free": Decimal("0.00"),
    "pro": Decimal("25.00"),
    "team": Decimal("99.00"),
    "enterprise": Decimal("499.00"),
}

COMPANIES = [
    "Acme Corp", "TechStart Inc", "DataFlow Systems", "CloudNine Labs",
    "Pixel Perfect", "Quantum Dynamics", "NexGen Solutions", "ByteForce",
    "InnovateTech", "ScaleUp Studios", "DevOps Pro", "CodeCraft",
    "StackHero", "LaunchPad AI", "Serverless Co", "MicroSaaS Ltd",
    "AppForge", "DataHive Analytics", "CloudBridge", "TurboAPI",
]

REGIONS = ["us-east-1", "us-west-1", "eu-central-1", "ap-southeast-1"]
PG_VERSIONS = ["14", "15", "16"]
PRODUCTS = ['Auth', 'Database', 'Storage', 'Edge Functions', 'Realtime', 'Dashboard', 'Billing', 'CLI', 'Other']


def random_project_ref():
    return ''.join(random.choices(string.ascii_lowercase, k=20))


def seed_customers(cur):
    print("  Seeding customers...")
    customers = []
    for _ in range(NUM_CUSTOMERS):
        signup_date = fake.date_between(start_date="-2y", end_date="-30d")
        company = random.choice(COMPANIES + [None] * 5)
        name = fake.name()
        email = f"{name.lower().replace(' ', '.')}@{fake.free_email_domain()}"
        country = fake.country_code()
        timezone = fake.timezone()

        cur.execute(
            """
            INSERT INTO customers (name, email, company, country, timezone, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (name, email, company, country, timezone, signup_date),
        )
        customers.append(cur.fetchone()[0])
    print(f"    [OK] {NUM_CUSTOMERS} customers created")
    return customers


def seed_organizations(cur, customers):
    print("  Seeding organizations...")
    orgs = []
    # Assign owners from a pool of customers
    owners = random.sample(customers, NUM_ORGS)
    for owner_id in owners:
        created_at = fake.date_between(start_date="-2y", end_date="-30d")
        name = f"{fake.company()} Org"
        billing_email = f"billing@{fake.domain_name()}"

        cur.execute(
            """
            INSERT INTO organizations (name, billing_email, owner_customer_id, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (name, billing_email, owner_id, created_at),
        )
        orgs.append({
            "id": cur.fetchone()[0],
            "owner_id": owner_id,
            "created_at": created_at
        })
    print(f"    [OK] {NUM_ORGS} organizations created")
    return orgs


def seed_projects_and_usage(cur, orgs):
    print("  Seeding projects & usage metrics...")
    projects = []
    
    for i in range(NUM_PROJECTS):
        org = random.choice(orgs)
        created_at = fake.date_between(start_date=org["created_at"], end_date="-10d")
        project_ref = random_project_ref()
        project_name = f"{fake.word().capitalize()} App"
        region = random.choice(REGIONS)
        postgres_version = random.choice(PG_VERSIONS)
        status = random.choices(['active', 'paused', 'suspended', 'coming_up'], weights=[0.8, 0.1, 0.05, 0.05])[0]

        cur.execute(
            """
            INSERT INTO projects (organization_id, project_ref, project_name, region, postgres_version, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (org["id"], project_ref, project_name, region, postgres_version, status, created_at),
        )
        project_id = cur.fetchone()[0]

        # Generate realistic usage
        if status == 'active':
            db_size = round(random.uniform(0.1, 50.0), 2)
            storage = round(random.uniform(0.1, 100.0), 2)
            bandwidth = round(random.uniform(1.0, 500.0), 2)
            api_reqs = random.randint(1000, 10000000)
            users = random.randint(10, 50000)
        else:
            db_size = round(random.uniform(0.1, 5.0), 2)
            storage = round(random.uniform(0.1, 10.0), 2)
            bandwidth = 0
            api_reqs = 0
            users = 0

        cur.execute(
            """
            INSERT INTO usage_metrics (project_id, database_size_gb, storage_gb, bandwidth_gb, api_requests, active_users)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (project_id, db_size, storage, bandwidth, api_reqs, users),
        )

        projects.append({
            "id": project_id,
            "org_id": org["id"],
            "owner_id": org["owner_id"],
            "db_size": db_size,
            "storage": storage,
            "api_reqs": api_reqs,
            "pg_version": postgres_version,
            "status": status,
            "created_at": created_at
        })
        
    print(f"    [OK] {NUM_PROJECTS} projects and usage metrics created")
    return projects


def seed_subscriptions_and_invoices(cur, orgs, projects):
    print("  Seeding subscriptions & invoices...")
    invoices_count = 0
    org_plans = {}
    
    for org in orgs:
        # Determine plan based on project usage
        org_projects = [p for p in projects if p["org_id"] == org["id"]]
        total_db_size = sum(p["db_size"] for p in org_projects)
        total_storage = sum(p["storage"] for p in org_projects)
        
        if total_db_size > 20 or total_storage > 50:
            plan = random.choice(["team", "enterprise"])
        elif total_db_size > 5 or total_storage > 5:
            plan = "pro"
        else:
            plan = "free"
            
        org_plans[org["id"]] = plan
        status = random.choices(["active", "past_due", "cancelled"], weights=[0.85, 0.1, 0.05])[0]
        started_at = org["created_at"]
        renewal_date = fake.date_between(start_date="+1d", end_date="+30d") if status == "active" else None
        
        cur.execute(
            """
            INSERT INTO subscriptions (organization_id, plan, status, monthly_cost, renewal_date, started_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (org["id"], plan, status, PLAN_MRR[plan], renewal_date, started_at),
        )

        # Generate invoices for paid plans
        if plan != "free":
            num_invoices = random.randint(1, 6)
            for j in range(num_invoices):
                inv_status = random.choices(["paid", "pending", "failed"], weights=[0.8, 0.1, 0.1])[0]
                amount = float(PLAN_MRR[plan])
                tax = round(amount * 0.1, 2)
                subtotal = amount
                invoice_number = f"INV-{org['id']}-{fake.unique.random_int(min=1000, max=9999)}"
                due_date = fake.date_between(start_date=started_at, end_date="today")
                paid_at = datetime.combine(due_date, datetime.min.time()) + timedelta(days=2) if inv_status == "paid" else None
                
                cur.execute(
                    """
                    INSERT INTO invoices (organization_id, invoice_number, subtotal, tax, currency, status, payment_method, billing_period, due_date, paid_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (org["id"], invoice_number, subtotal, tax, "USD", inv_status, "card", "monthly", due_date, paid_at),
                )
                invoices_count += 1
                
    print(f"    [OK] {len(orgs)} subscriptions created")
    print(f"    [OK] {invoices_count} invoices created")
    return org_plans


def seed_agents(cur):
    print("  Seeding agents...")
    agent_ids = []
    agent_names = ["Sarah Chen", "Marcus Johnson", "Priya Patel", "Alex Rodriguez", "Jordan Kim"]
    for name in agent_names:
        email = f"{name.lower().replace(' ', '.')}@support.supabase.io"
        cur.execute(
            "INSERT INTO agents (name, email) VALUES (%s, %s) RETURNING id",
            (name, email),
        )
        agent_ids.append(cur.fetchone()[0])
    print(f"    [OK] {NUM_AGENTS} agents created")
    return agent_ids


def generate_story_ticket(project):
    """Generates a realistic ticket based on project state."""
    # Logic matching realistic states
    if project["storage"] > 90.0:
        return ("Storage upload denied (Quota Exceeded)", "bug", "Storage", "urgent", 
                "We are getting 403 errors when uploading to our buckets. Is there a hard limit?")
    elif project["db_size"] > 40.0:
        return ("Database read replica lag", "technical", "Database", "high",
                "Our read replicas are lagging by several minutes. This is affecting user dashboards.")
    elif project["api_reqs"] > 5000000:
        return ("Connection pooling timeout", "technical", "Database", "high",
                "PgBouncer is rejecting connections under high load. How can we increase the pool size?")
    elif project["status"] == "suspended":
        return ("Project suspended unexpectedly", "billing", "Billing", "urgent",
                "Our project was suspended but we just paid our invoice. Please reactivate immediately.")
    elif project["pg_version"] == "14":
        return ("Database migration failed", "bug", "Database", "medium",
                "Tried to upgrade to PG 15 but the migration script hung.")
    else:
        # Random generic SaaS issues
        generics = [
            ("Row Level Security policy not working", "technical", "Database", "medium", "I added an RLS policy for the users table but everyone can still read everything."),
            ("Auth redirect loop", "bug", "Auth", "high", "After successful OAuth login with Google, users are stuck in a redirect loop on the client side."),
            ("Realtime websocket disconnected", "bug", "Realtime", "high", "Our chat app keeps dropping the websocket connection after 5 minutes of inactivity."),
            ("Edge Function deployment failed", "bug", "Edge Functions", "medium", "Getting an Esbuild error when deploying my edge function via CLI."),
            ("Dashboard slow loading", "technical", "Dashboard", "low", "The table editor in the dashboard takes 10+ seconds to load our larger tables."),
            ("OAuth callback error", "bug", "Auth", "medium", "Getting 'invalid grant' error on the callback URL for GitHub auth."),
            ("pgvector extension missing", "technical", "Database", "medium", "Can't seem to enable pgvector, it says extension not found.")
        ]
        return random.choice(generics)


def seed_tickets_and_messages(cur, projects, agent_ids):
    print("  Seeding tickets & messages...")
    tickets_created = 0
    msgs_created = 0

    for project in projects:
        # Generate 1-2 tickets per project
        for _ in range(random.randint(1, 2)):
            subject, category, affected_product, severity, initial_msg = generate_story_ticket(project)
            agent_id = random.choice(agent_ids)
            status = random.choice(["open", "in_progress", "resolved", "closed"])
            
            created_at = fake.date_time_between(start_date=project["created_at"], end_date="now")
            resolved_at = created_at + timedelta(hours=random.randint(2, 48)) if status in ("resolved", "closed") else None

            cur.execute(
                """
                INSERT INTO tickets (customer_id, project_id, agent_id, subject, category, affected_product, status, severity, created_at, resolved_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (project["owner_id"], project["id"], agent_id, subject, category, affected_product, status, severity, created_at, resolved_at),
            )
            ticket_id = cur.fetchone()[0]
            tickets_created += 1

            # Insert initial message
            cur.execute(
                "INSERT INTO ticket_messages (ticket_id, sender_type, message, created_at) VALUES (%s, %s, %s, %s)",
                (ticket_id, "customer", initial_msg, created_at)
            )
            msgs_created += 1

            # Agent reply
            if status != "open":
                agent_reply = "I'm looking into this right now. Can you provide your project ref just in case?"
                reply_time = created_at + timedelta(minutes=random.randint(10, 120))
                cur.execute(
                    "INSERT INTO ticket_messages (ticket_id, sender_type, message, created_at) VALUES (%s, %s, %s, %s)",
                    (ticket_id, "agent", agent_reply, reply_time)
                )
                msgs_created += 1
                
                # Internal note
                if random.random() > 0.7:
                    note = "User has high usage, escalating to tier 2."
                    cur.execute(
                        "INSERT INTO ticket_messages (ticket_id, sender_type, message, internal_note, created_at) VALUES (%s, %s, %s, %s, %s)",
                        (ticket_id, "agent", note, True, reply_time + timedelta(minutes=5))
                    )
                    msgs_created += 1

    print(f"    [OK] {tickets_created} tickets created")
    print(f"    [OK] {msgs_created} ticket messages created")
    return tickets_created, msgs_created


def main():
    print("=" * 60)
    print("Enterprise Data Copilot — Seed Script")
    print("=" * 60)
    print(f"\nConnecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Clear existing data
        print("\n[1/7] Clearing existing data...")
        tables = [
            "ticket_messages", "tickets", "invoices", "subscriptions",
            "usage_metrics", "projects", "organizations", "agents", "customers"
        ]
        for table in tables:
            cur.execute(f"TRUNCATE {table} CASCADE")
        print("    [OK] All tables cleared")

        print("\n[2/7] Seeding core hierarchy...")
        customers = seed_customers(cur)
        orgs = seed_organizations(cur, customers)
        projects = seed_projects_and_usage(cur, orgs)

        print("\n[3/7] Seeding billing & invoices...")
        seed_subscriptions_and_invoices(cur, orgs, projects)

        print("\n[4/7] Seeding agents...")
        agent_ids = seed_agents(cur)

        print("\n[5/7] Seeding support tickets...")
        seed_tickets_and_messages(cur, projects, agent_ids)

        conn.commit()
        print("\n[OK] Seed complete! All realistic data committed.")

    except Exception as e:
        conn.rollback()
        print(f"\n[FAIL] Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
