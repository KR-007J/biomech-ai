import random
import sys
sys.path.insert(0, 'backend')

from ab_testing import ABTestingEngine

random.seed(42)
engine = ABTestingEngine()
exp_id = engine.create_experiment('test', variants=['control', 'variant'])
engine.start_experiment(exp_id)

for i in range(1000):
    user_id = f'user-{i}'
    variant = engine.allocate_user(exp_id, user_id)
    converted = (i % 100) < (15 if variant == 'variant' else 10)
    engine.record_conversion(exp_id, user_id, converted)

results = engine.analyze_results(exp_id)
print(f"Control: {results['control']['conversion_rate']:.1%}")
print(f"Variant: {results['variant']['conversion_rate']:.1%}")
print(f"Control users: {results['control']['users']}, conversions: {results['control']['conversions']}")
print(f"Variant users: {results['variant']['users']}, conversions: {results['variant']['conversions']}")
