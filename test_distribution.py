from utils.distribution_optimizer import DistributionOptimizer

# Initialize optimizer
optimizer = DistributionOptimizer()

# Test data - with proper coordinates structure
warehouses = [
    {'name': 'Lumbung Desa A', 'coordinates': {'lat': -7.0, 'lng': 112.0}, 'capacity': 5000},
    {'name': 'Lumbung Desa B', 'coordinates': {'lat': -7.1, 'lng': 112.1}, 'capacity': 3000}
]

merchants = [
    {'name': 'Pedagang X', 'coordinates': {'lat': -7.05, 'lng': 112.05}, 'demand': 1000},
    {'name': 'Pedagang Y', 'coordinates': {'lat': -7.08, 'lng': 112.08}, 'demand': 800}
]

# Test route optimization
print("Testing Distribution Optimizer...")
routes = optimizer.optimize_distribution_routes(warehouses, merchants)
print('\nOptimized Routes:')
for i, route in enumerate(routes):
    print(f'Route {i+1}: {route["route"]}')
    print(f'Total Distance: {route["total_distance"]} km')
    print(f'Total Cost: Rp {route["total_cost"]:,}')
    print('---')

# Test cost calculation with a simple route
simple_route = merchants[0:1]  # Just the first merchant
warehouse_coord = (warehouses[0]['coordinates']['lat'], warehouses[0]['coordinates']['lng'])
cost_analysis = optimizer.calculate_distribution_cost(simple_route, warehouse_coord)
print('\nCost analysis for simple route:')
print(f'Total Distance: {cost_analysis["total_distance_km"]} km')
print(f'Total Cost: Rp {cost_analysis["total_cost_idr"]:,}')
print(f'Fuel Cost: Rp {cost_analysis["fuel_cost_idr"]:,}')
print(f'Driver Cost: Rp {cost_analysis["driver_cost_idr"]:,}')

print("\nDistribution optimizer test completed successfully!")