#!/usr/bin/env python
"""Validate GitHub Actions workflow"""
import sys

import yaml

try:
    with open(".github/workflows/ci-cd.yml", "r", encoding="utf-8") as f:
        workflow = yaml.safe_load(f)

    print("OK - Workflow YAML is valid")
    print()
    print("Workflow Structure:")
    name = workflow.get("name")
    jobs = list(workflow.get("jobs", {}).keys())
    print(f"  Name: {name}")
    print(f"  Jobs: {jobs}")
    print()
    
    # Check deployment job
    deploy_job = workflow.get("jobs", {}).get("deploy", {})
    if deploy_job:
        print("OK - Deploy job found")
        print(f'  Runs on: {deploy_job.get("runs-on")}')
        print(f'  Needs: {deploy_job.get("needs")}')
        if_condition = deploy_job.get("if")
        print(f"  If: {if_condition}")
        
        # Check steps
        steps = deploy_job.get("steps", [])
        print(f"  Steps: {len(steps)}")
        for i, step in enumerate(steps, 1):
            step_name = step.get("name", "Unnamed")
            print(f"    {i}. {step_name}")
    else:
        print("WARN - No deploy job found!")
        
    print()
    print("OK - Workflow validation complete!")
    
except yaml.YAMLError as e:
    print(f"ERROR - YAML Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR - {e}")
    sys.exit(1)
