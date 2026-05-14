from app import create_app
from app.models import db, Consignment
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
            
            # Add dummy consignments
            consignments = [
                Consignment(
                    consignment_number="GRAM-SCS-2024-001",
                    status="In Transit",
                    eta="2024-03-05 14:30"
                ),
                Consignment(
                    consignment_number="GRAM-SCS-2024-002",
                    status="Out for Delivery",
                    eta="2024-03-04 18:00"
                ),
                Consignment(
                    consignment_number="GRAM-SCS-2024-003",
                    status="Delivered",
                    eta="2024-03-03 10:00"
                ),
                Consignment(
                    consignment_number="GRAM-SCS-2024-004",
                    status="Pickup Scheduled",
                    eta="2024-03-06 09:00"
                ),
                Consignment(
                    consignment_number="GRAM-SCS-2024-005",
                    status="In Transit",
                    eta="2024-03-05 16:45"
                )
            ]
            
            logger.info(f"Adding {len(consignments)} dummy consignments...")
            for consignment in consignments:
                db.session.add(consignment)
            
            db.session.commit()
            logger.info(f"✓ Successfully added {len(consignments)} dummy consignments to the database")
            print("\nTest with these consignment numbers:")
            for c in consignments:
                print(f"  - {c.consignment_number} ({c.status})")
        
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
