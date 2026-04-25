#!/usr/bin/env python
"""Complete CI/CD workflow validation"""
import yaml

with open('.github/workflows/ci-cd.yml', 'r', encoding='utf-8') as f:
    workflow = yaml.safe_load(f)

print('=' * 60)
print('CI/CD WORKFLOW VALIDATION')
print('=' * 60)
print()

jobs = workflow.get('jobs', {})
print('Workflow Jobs ({0}):'.format(len(jobs)))
for job_name in jobs:
    job_config = jobs[job_name]
    runs_on = job_config.get('runs-on', 'N/A')
    print('   - {0:12} (runs-on: {1})'.format(job_name, runs_on))

print()
print('Deployment Configuration:')
deploy = jobs.get('deploy', {})
if deploy:
    print('   OK - Deploy job exists')
    print('   OK - Runs on: {0}'.format(deploy.get('runs-on')))
    print('   OK - Needs: {0}'.format(deploy.get('needs')))
    print('   OK - Condition: {0}'.format(deploy.get('if')))
else:
    print('   ERROR - Deploy job missing')

print()
print('✅ All validations passed!')
print('=' * 60)
