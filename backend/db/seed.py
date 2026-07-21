"""
Enterprise Data Copilot — Seed Script
Generates realistic synthetic data for all 6 business tables.

Usage:
    python seed.py

Requires:
    pip install faker psycopg2-binary python-dotenv

Data distribution (from spec):
    - 50 customers (mix of all 4 plans)
    - 50 subscriptions (1 per customer, ~10% past_due/cancelled)
    - 150 invoices (2-4 per customer, ~15% failed/pending)
    - 5 agents
    - 80 tickets (spread across categories/statuses)
    - 200 ticket_messages (2-4 per ticket)
"""

import os
import random
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
NUM_AGENTS = 5
NUM_TICKETS = 80
NUM_TICKET_MESSAGES = 200
INVOICES_PER_CUSTOMER = (2, 4)  # min, max

PLANS = ["free", "pro", "team", "enterprise"]
PLAN_WEIGHTS = [0.30, 0.35, 0.20, 0.15]  # distribution

PLAN_MRR = {
    "free": Decimal("0.00"),
    "pro": Decimal("25.00"),
    "team": Decimal("99.00"),
    "enterprise": Decimal("499.00"),
}

SUB_STATUSES = ["active", "past_due", "cancelled", "trialing"]
SUB_STATUS_WEIGHTS = [0.70, 0.05, 0.05, 0.20]  # ~10% past_due/cancelled

INVOICE_STATUSES = ["paid", "pending", "failed", "refunded"]
INVOICE_STATUS_WEIGHTS = [0.75, 0.10, 0.05, 0.10]  # ~15% non-paid

TICKET_CATEGORIES = ["billing", "technical", "account", "feature_request", "bug"]
TICKET_STATUSES = ["open", "in_progress", "resolved", "closed"]
TICKET_PRIORITIES = ["low", "medium", "high", "urgent"]

# Realistic ticket subjects for a SaaS support system
TICKET_SUBJECTS = [
    "Can't connect to database",
    "Billing charged twice",
    "How do I add RLS policy",
    "Connection timeout on edge functions",
    "Storage bucket permission denied",
    "Can't reset password",
    "API rate limit hit unexpectedly",
    "Dashboard loading slow",
    "Migration failed on production",
    "Row level security not working",
    "Webhook not firing",
    "Can't invite team member",
    "Invoice amount seems wrong",
    "Need to upgrade plan",
    "Database backup not working",
    "Realtime subscription dropping",
    "Auth redirect loop",
    "SSL certificate error",
    "Function deployment failed",
    "Can't delete project",
    "Storage upload size limit",
    "PostgREST returning 500",
    "Need help with database schema",
    "Email confirmation not sent",
    "Two-factor auth locked out",
    "Cron job not executing",
    "Read replica lag too high",
    "Need custom domain setup",
    "API returns wrong data format",
    "Supabase CLI not connecting",
    "Database disk usage growing fast",
    "Can't access logs",
    "Need to transfer project ownership",
    "Branching not working",
    "Foreign key constraint error",
    "Full text search not returning results",
    "GraphQL endpoint not responding",
    "Need help with triggers",
    "Subscription renewal failed",
    "Account locked after failed payments",
]

# Realistic agent/customer message templates
CUSTOMER_MESSAGES = [
    "Hi, I'm having trouble with {subject}. Can you help?",
    "This issue has been happening since yesterday. {subject}.",
    "I've already tried restarting but the problem persists.",
    "This is affecting our production system. Please prioritize.",
    "Thanks for looking into this. Any update?",
    "I've attached screenshots showing the error.",
    "Can you escalate this? It's been open for a while.",
    "We're a paying customer and this is impacting our business.",
    "Is there a workaround in the meantime?",
    "The error message says: connection refused.",
]

AGENT_MESSAGES = [
    "Hi! I'm looking into this for you now.",
    "Could you share the error logs from your dashboard?",
    "I've identified the issue. Let me apply a fix.",
    "This is a known issue and our team is working on it.",
    "I've escalated this to our engineering team.",
    "The fix has been deployed. Can you verify it's working?",
    "This should be resolved now. Please let me know if it recurs.",
    "I'm going to need a bit more information to debug this.",
    "We've released a patch for this. Please try again.",
    "Closing this ticket as resolved. Don't hesitate to reopen if needed.",
]

COMPANIES = [
    "Acme Corp", "TechStart Inc", "DataFlow Systems", "CloudNine Labs",
    "Pixel Perfect", "Quantum Dynamics", "NexGen Solutions", "ByteForce",
    "InnovateTech", "ScaleUp Studios", "DevOps Pro", "CodeCraft",
    "StackHero", "LaunchPad AI", "Serverless Co", "MicroSaaS Ltd",
    "AppForge", "DataHive Analytics", "CloudBridge", "TurboAPI",
    None, None, None, None, None,  # ~20% have no company
]


def seed_customers(cur):
    """Generate 50 customers with realistic distribution."""
    print("  Seeding customers...")
    customers = []
    for i in range(NUM_CUSTOMERS):
        plan = random.choices(PLANS, weights=PLAN_WEIGHTS, k=1)[0]
        signup_date = fake.date_between(start_date="-2y", end_date="-30d")
        company = random.choice(COMPANIES)
        name = fake.name()
        email = f"{name.lower().replace(' ', '.')}@{fake.free_email_domain()}"

        cur.execute(
            """
            INSERT INTO customers (name, email, company, signup_date, plan)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (name, email, company, signup_date, plan),
        )
        customer_id = cur.fetchone()[0]
        customers.append({
            "id": customer_id,
            "plan": plan,
            "signup_date": signup_date,
        })
    print(f"    [OK] {NUM_CUSTOMERS} customers created")
    return customers


def seed_subscriptions(cur, customers):
    """Generate 1 subscription per customer."""
    print("  Seeding subscriptions...")
    for c in customers:
        status = random.choices(SUB_STATUSES, weights=SUB_STATUS_WEIGHTS, k=1)[0]
        mrr = PLAN_MRR[c["plan"]]
        started_at = c["signup_date"]
        renewal_date = None
        if status in ("active", "trialing"):
            renewal_date = fake.date_between(start_date="+1d", end_date="+90d")

        cur.execute(
            """
            INSERT INTO subscriptions (customer_id, plan_name, status, mrr, renewal_date, started_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (c["id"], c["plan"], status, mrr, renewal_date, started_at),
        )
    print(f"    [OK] {len(customers)} subscriptions created")


def seed_invoices(cur, customers):
    """Generate 2-4 invoices per customer (150 total target)."""
    print("  Seeding invoices...")
    count = 0
    for c in customers:
        num_invoices = random.randint(*INVOICES_PER_CUSTOMER)
        base_amount = float(PLAN_MRR[c["plan"]]) if PLAN_MRR[c["plan"]] > 0 else random.uniform(5, 25)

        for j in range(num_invoices):
            status = random.choices(INVOICE_STATUSES, weights=INVOICE_STATUS_WEIGHTS, k=1)[0]
            amount = round(base_amount * random.uniform(0.8, 1.2), 2)
            due_date = fake.date_between(start_date=c["signup_date"], end_date="today")
            paid_at = None
            if status == "paid":
                paid_at = datetime.combine(due_date, datetime.min.time()) + timedelta(
                    days=random.randint(0, 5)
                )

            cur.execute(
                """
                INSERT INTO invoices (customer_id, amount, status, due_date, paid_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (c["id"], amount, status, due_date, paid_at),
            )
            count += 1
    print(f"    [OK] {count} invoices created")


def seed_agents(cur):
    """Generate 5 support agents."""
    print("  Seeding agents...")
    agent_ids = []
    agent_names = [
        "Sarah Chen", "Marcus Johnson", "Priya Patel",
        "Alex Rodriguez", "Jordan Kim"
    ]
    for name in agent_names:
        email = f"{name.lower().replace(' ', '.')}@support.supabase.io"
        cur.execute(
            """
            INSERT INTO agents (name, email)
            VALUES (%s, %s)
            RETURNING id
            """,
            (name, email),
        )
        agent_ids.append(cur.fetchone()[0])
    print(f"    [OK] {NUM_AGENTS} agents created")
    return agent_ids


def seed_tickets(cur, customers, agent_ids):
    """Generate 80 tickets with realistic distribution."""
    print("  Seeding tickets...")
    ticket_ids = []
    subjects_pool = TICKET_SUBJECTS.copy()

    for i in range(NUM_TICKETS):
        customer = random.choice(customers)
        agent_id = random.choice(agent_ids)
        subject = random.choice(subjects_pool)
        category = random.choice(TICKET_CATEGORIES)
        status = random.choice(TICKET_STATUSES)
        priority = random.choice(TICKET_PRIORITIES)

        created_at = fake.date_time_between(start_date="-6M", end_date="now")
        resolved_at = None
        if status in ("resolved", "closed"):
            resolved_at = created_at + timedelta(
                hours=random.randint(1, 72)
            )

        cur.execute(
            """
            INSERT INTO tickets (customer_id, agent_id, subject, category, status, priority, created_at, resolved_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (customer["id"], agent_id, subject, category, status, priority, created_at, resolved_at),
        )
        ticket_ids.append(cur.fetchone()[0])
    print(f"    [OK] {NUM_TICKETS} tickets created")
    return ticket_ids


def seed_ticket_messages(cur, ticket_ids):
    """Generate ~200 ticket messages (2-4 per ticket)."""
    print("  Seeding ticket messages...")
    count = 0
    for ticket_id in ticket_ids:
        num_messages = random.randint(2, 4)
        base_time = fake.date_time_between(start_date="-6M", end_date="-1d")

        for j in range(num_messages):
            sender_type = "customer" if j % 2 == 0 else "agent"
            if sender_type == "customer":
                message = random.choice(CUSTOMER_MESSAGES).format(
                    subject=random.choice(TICKET_SUBJECTS)
                )
            else:
                message = random.choice(AGENT_MESSAGES)

            created_at = base_time + timedelta(hours=j * random.randint(1, 12))

            cur.execute(
                """
                INSERT INTO ticket_messages (ticket_id, sender_type, message, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (ticket_id, sender_type, message, created_at),
            )
            count += 1

    print(f"    [OK] {count} ticket messages created")


def verify_counts(cur):
    """Verify row counts match expectations."""
    print("\n  Verifying row counts...")
    tables = [
        ("customers", NUM_CUSTOMERS),
        ("subscriptions", NUM_CUSTOMERS),
        ("agents", NUM_AGENTS),
        ("tickets", NUM_TICKETS),
    ]
    all_ok = True
    for table, expected in tables:
        cur.execute(f"SELECT count(*) FROM {table}")
        actual = cur.fetchone()[0]
        status = "[OK]" if actual == expected else "[FAIL]"
        if actual != expected:
            all_ok = False
        print(f"    {status} {table}: {actual} rows (expected {expected})")

    # Invoices and messages have variable counts
    for table in ["invoices", "ticket_messages"]:
        cur.execute(f"SELECT count(*) FROM {table}")
        actual = cur.fetchone()[0]
        print(f"    [OK] {table}: {actual} rows")

    return all_ok


def main():
    print("=" * 60)
    print("Enterprise Data Copilot — Seed Script")
    print("=" * 60)
    print(f"\nConnecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Clear existing data (in reverse FK order)
        print("\n[1/7] Clearing existing data...")
        for table in [
            "ticket_messages", "tickets", "invoices",
            "subscriptions", "agents", "customers"
        ]:
            cur.execute(f"TRUNCATE {table} CASCADE")
        print("    [OK] All tables cleared")

        # Seed data
        print("\n[2/7] Seeding customers...")
        customers = seed_customers(cur)

        print("\n[3/7] Seeding subscriptions...")
        seed_subscriptions(cur, customers)

        print("\n[4/7] Seeding invoices...")
        seed_invoices(cur, customers)

        print("\n[5/7] Seeding agents...")
        agent_ids = seed_agents(cur)

        print("\n[6/7] Seeding tickets...")
        ticket_ids = seed_tickets(cur, customers, agent_ids)

        print("\n[7/7] Seeding ticket messages...")
        seed_ticket_messages(cur, ticket_ids)

        # Verify
        ok = verify_counts(cur)

        if ok:
            conn.commit()
            print("\n[OK] Seed complete! All data committed.")
        else:
            conn.rollback()
            print("\n[FAIL] Verification failed. Transaction rolled back.")

    except Exception as e:
        conn.rollback()
        print(f"\n[FAIL] Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
