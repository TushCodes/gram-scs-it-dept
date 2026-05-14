#!/usr/bin/env python
"""Script to add 100 dummy consignments to the database."""

import os
import sys
from datetime import datetime, timedelta

# Set development environment
os.environ['FLASK_ENV'] = 'development'
os.environ['SECRET_KEY'] = 'dev-secret-key-12345'
os.environ['ADMIN_PASSWORD_HASH'] = 'scrypt:32768:8:1$njZCkiEimG4sP37X$45f25bb2b63de677fc1737e78127f9324884cfdabefd96627da1f8ff5f94ef1c49dda9422b6749fc26a4b82b77ea1895cb3c4c32b37669fab5d49c14b93029'

from app import create_app, db
from app.models import Consignment

app = create_app()

# Statuses
statuses = ['Pickup Scheduled', 'In Transit', 'Out for Delivery', 'Delivered']

# Sample pickup tags
pickup_tags = ['Main Office', 'Branch A', 'Branch B', 'Warehouse', 'Distribution Center']

# Sample drop tags
drop_tags = ['Customer Location', 'Hub', 'Warehouse', 'Distribution', 'Final Destination']

# Indian pincodes
pincodes = [
    '110001', '110002', '110003', '110004', '110005',  # Delhi
    '400001', '400002', '400003', '400004', '400005',  # Mumbai
    '560001', '560002', '560003', '560004', '560005',  # Bangalore
    '700001', '700002', '700003', '700004', '700005',  # Kolkata
    '600001', '600002', '600003', '600004', '600005',  # Chennai
    '411001', '411002', '411003', '411004', '411005',  # Pune
    '421001', '421002', '421003', '421004', '421005',  # Thane
]

# Sample addresses
pickup_addresses = [
    '123 Business Park, New Delhi',
    '456 Corporate Tower, Mumbai',
    '789 Tech Park, Bangalore',
    '321 Industrial Area, Kolkata',
    '654 Commercial Hub, Chennai',
    '987 Warehouse Complex, Pune',
    '159 Distribution Center, Thane',
]

drop_addresses = [
    '100 Customer Lane, Delhi',
    '200 Delivery Point, Mumbai',
    '300 Destination Ave, Bangalore',
    '400 Final Stop, Kolkata',
    '500 End Location, Chennai',
    '600 Customer Address, Pune',
    '700 Recipient Place, Thane',
]

def add_dummy_consignments():
    """Add 100 dummy consignments to the database."""
    
    with app.app_context():
        # Check if data already exists
        existing_count = Consignment.query.count()
        if existing_count > 0:
            print(f"Database already has {existing_count} consignments. Skipping insertion.")
            return
        
        consignments = []
        base_date = datetime.now()
        
        for i in range(1, 101):
            consignment_number = f"CON-2026-{i:04d}"
            status = statuses[i % len(statuses)]
            pickup_pincode = pincodes[i % len(pincodes)]
            drop_pincode = pincodes[(i + 5) % len(pincodes)]
            pickup_tag = pickup_tags[i % len(pickup_tags)]
            drop_tag = drop_tags[i % len(drop_tags)]
            pickup_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            drop_date = (base_date + timedelta(days=i+2)).strftime("%Y-%m-%d")
            pickup_address = pickup_addresses[i % len(pickup_addresses)]
            drop_address = drop_addresses[i % len(drop_addresses)]
            
            consignment = Consignment(
                consignment_number=consignment_number,
                status=status,
                pickup_pincode=pickup_pincode,
                pickup_address=pickup_address,
                pickup_tag=pickup_tag,
                pickup_date=pickup_date,
                drop_pincode=drop_pincode,
                drop_address=drop_address,
                drop_tag=drop_tag,
                drop_date=drop_date,
                eta=""
            )
            consignments.append(consignment)
        
        # Insert all at once
        db.session.add_all(consignments)
        db.session.commit()
        
        print(f"✅ Successfully added {len(consignments)} dummy consignments!")
        print(f"Total consignments in database: {Consignment.query.count()}")

if __name__ == '__main__':
    try:
        add_dummy_consignments()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
