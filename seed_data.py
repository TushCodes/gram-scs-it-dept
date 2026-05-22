from app import create_app
from app.models import db, Consignment, Lead
from sqlalchemy.exc import IntegrityError, OperationalError
import sys
import logging

logger = logging.getLogger(__name__)

try:
    app = create_app()

    with app.app_context():
        try:
            # Clear existing data
            logger.info("Clearing existing consignments...")
            Consignment.query.delete()

            logger.info("Clearing existing leads...")
            Lead.query.delete()
            
            # Add dummy consignments
            consignments = [
                Consignment(
                    consignment_number="GS-2024-001",
                    status="In Transit",
                    eta="2024-03-05 14:30"
                ),
                Consignment(
                    consignment_number="GS-2024-002",
                    status="Out for Delivery",
                    eta="2024-03-04 18:00"
                ),
                Consignment(
                    consignment_number="GS-2024-003",
                    status="Delivered",
                    eta="2024-03-03 10:00"
                ),
                Consignment(
                    consignment_number="GS-2024-004",
                    status="Pickup Scheduled",
                    eta="2024-03-06 09:00"
                ),
                Consignment(
                    consignment_number="GS-2024-005",
                    status="In Transit",
                    eta="2024-03-05 16:45"
                )
            ]
            
            logger.info(f"Adding {len(consignments)} dummy consignments...")
            for consignment in consignments:
                db.session.add(consignment)

            leads = [
                Lead(
                    name="Aarav Mehta",
                    email="aarav.mehta@example.com",
                    phone="+91 98765 43210",
                    subject="Warehouse Enquiry",
                    message="Need details for 3PL warehousing in Mumbai.",
                ),
                Lead(
                    name="Priya Nair",
                    email="priya.nair@example.com",
                    phone="+91 98111 22334",
                    subject="Transport Partnership",
                    message="Looking for a long-term transport partner for South India routes.",
                ),
                Lead(
                    name="Global Imports LLC",
                    email="ops@globalimports.example",
                    phone="+1 (415) 555-0198",
                    subject="International Freight",
                    message="Requesting a callback about import clearance and freight forwarding.",
                ),
                Lead(
                    name="No Phone Lead",
                    email="nophone@example.com",
                    phone=None,
                    subject="Missing Phone",
                    message="This record is intentionally missing a phone number.",
                ),
                Lead(
                    name="Whitespace Phone Lead",
                    email="whitespace@example.com",
                    phone="   ",
                    subject="Whitespace Phone",
                    message="This record uses whitespace only for the phone field.",
                ),
                Lead(
                    name="Short Inquiry",
                    email="short.inquiry@example.com",
                    phone="99999 88888",
                    subject="Quick Question",
                    message="Please share the contact person for contract logistics.",
                ),
                Lead(
                    name="Bulk Operations Team",
                    email="bulk.ops@example.com",
                    phone="+91-90000-11111",
                    subject="Bulk Dispatch",
                    message="We need a dispatch plan for weekly high-volume shipments.",
                ),
            ]

            logger.info(f"Adding {len(leads)} dummy leads...")
            for lead in leads:
                db.session.add(lead)
            
            db.session.commit()
            logger.info(f"✓ Successfully added {len(consignments)} dummy consignments to the database")
            logger.info(f"✓ Successfully added {len(leads)} dummy leads to the database")
            print("\nTest with these consignment numbers:")
            for c in consignments:
                print(f"  - {c.consignment_number} ({c.status})")

            print("\nSeeded lead email addresses:")
            for lead in leads:
                print(f"  - {lead.email} | phone={lead.phone!r}")
        
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Database integrity error (duplicate data?): {e}")
            sys.exit(1)
        
        except OperationalError as e:
            db.session.rollback()
            logger.error(f"Database operational error: {e}")
            sys.exit(1)
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error while seeding data: {e}", exc_info=True)
            sys.exit(1)

except Exception as e:
    logger.error(f"Failed to create application: {e}", exc_info=True)
    sys.exit(1)
