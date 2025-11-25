from utils.database import MongoDBConnection
from utils.geocoding import GeocodingService

# Test database connection
db = MongoDBConnection.get_database()
print('Database connection successful')

# Check if geospatial indexes exist
collections = ['farmers', 'merchants', 'warehouses']
for collection_name in collections:
    collection = db[collection_name]
    indexes = list(collection.list_indexes())
    print(f'\nIndexes for {collection_name}:')
    for index in indexes:
        print(f'  - {index["name"]}: {index["key"]}')

# Test inserting a farmer with coordinates
service = GeocodingService()
coords = service.geocode_address('Bandung, Jawa Barat, Indonesia')
print(f'\nTest coordinates for Bandung: {coords}')

# Test finding nearby locations (if we have data)
if coords:
    # Create a test farmer with coordinates in GeoJSON format
    test_farmer = {
        'name': 'Petani Test',
        'address': 'Bandung, Jawa Barat, Indonesia',
        'coordinates': {
            'type': 'Point',
            'coordinates': [coords['lng'], coords['lat']]
        },
        'phone': '08123456789',
        'land_area': 2.5,
        'crop_type': 'Padi'
    }
    
    # Insert test farmer
    result = db.farmers.insert_one(test_farmer)
    print(f'Inserted test farmer with ID: {result.inserted_id}')
    
    # Test geospatial query
    nearby_query = {
        'coordinates': {
            '$near': {
                '$geometry': {
                    'type': 'Point',
                    'coordinates': [coords['lng'], coords['lat']]
                },
                '$maxDistance': 10000  # 10km radius in meters
            }
        }
    }
    
    nearby_farmers = list(db.farmers.find(nearby_query))
    print(f'Found {len(nearby_farmers)} farmers within 10km of Bandung')

print('\nDatabase and geocoding integration test completed!')