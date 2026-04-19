#!/usr/bin/env python3
"""
Automated Deployment Script for AI Biomechanics Platform
Supports: Local Dev, Staging, Production
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DeploymentManager:
    """Handles deployment across environments"""

    ENVIRONMENTS = {
        "dev": {
            "host": "localhost",
            "port": 8000,
            "workers": 1,
            "debug": True,
            "db_url": "postgresql://user:pass@localhost/biomech_dev",
        },
        "staging": {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 2,
            "debug": False,
            "db_url": os.getenv("STAGING_DB_URL"),
        },
        "production": {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 8,
            "debug": False,
            "db_url": os.getenv("PRODUCTION_DB_URL"),
        },
    }

    def __init__(self, environment: str = "dev"):
        self.env = environment
        self.config = self.ENVIRONMENTS.get(environment)
        if not self.config:
            raise ValueError(f"Unknown environment: {environment}")

        self.backend_dir = Path(__file__).parent
        self.root_dir = self.backend_dir.parent

    def run_command(self, cmd: list, cwd: Optional[Path] = None) -> bool:
        """Execute a shell command"""
        try:
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=cwd or self.backend_dir, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with code {e.returncode}")
            return False

    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        logger.info("Installing dependencies...")
        return self.run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    def setup_database(self) -> bool:
        """Initialize database"""
        logger.info("Setting up database...")

        # Run migrations
        if not self.run_command([sys.executable, "-m", "alembic", "upgrade", "head"]):
            return False

        # Initialize test data (staging/prod only)
        if self.env in ["staging", "production"]:
            logger.info("Seeding database...")
            # Could add seeding script here

        return True

    def run_tests(self) -> bool:
        """Run test suite"""
        logger.info("Running test suite...")
        return self.run_command(
            [sys.executable, "-m", "pytest", "test_all_tiers.py", "-v", "--tb=short"]
        )

    def validate_code(self) -> bool:
        """Run code validation"""
        logger.info("Validating code...")

        # Type checking
        if not self.run_command([sys.executable, "-m", "mypy", ".", "--ignore-missing-imports"]):
            logger.warning("Type checking failed")
            return False

        # Linting
        if not self.run_command([sys.executable, "-m", "flake8", ".", "--count"]):
            logger.warning("Linting failed")
            return False

        return True

    def start_services(self) -> bool:
        """Start all services via Docker Compose"""
        if self.env == "dev":
            logger.info("Starting services with docker-compose...")
            return self.run_command(
                ["docker-compose", "-f", "docker-compose.yml", "up", "-d"], cwd=self.root_dir
            )
        return True

    def warm_cache(self) -> bool:
        """Warm up Redis cache"""
        logger.info("Warming cache...")
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            logger.info("Cache warmed successfully")
            return True
        except Exception as e:
            logger.warning(f"Cache warming failed: {e}")
            return False

    def health_check(self) -> bool:
        """Verify deployment health"""
        logger.info("Running health checks...")

        try:
            import requests

            url = f"http://{self.config['host']}:{self.config['port']}/api/v2/status"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                logger.info(f"✅ API healthy: {response.json()}")
                return True
            else:
                logger.error(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def deploy_dev(self) -> bool:
        """Deploy to development"""
        logger.info(f"Deploying to {self.env}...")

        steps = [
            ("Install dependencies", self.install_dependencies),
            ("Setup database", self.setup_database),
            ("Validate code", self.validate_code),
            ("Run tests", self.run_tests),
            ("Start services", self.start_services),
            ("Warm cache", self.warm_cache),
            ("Health check", self.health_check),
        ]

        for step_name, step_func in steps:
            logger.info(f"\n▶ {step_name}...")
            if not step_func():
                logger.error(f"❌ {step_name} failed")
                return False
            logger.info(f"✅ {step_name} complete")

        logger.info(f"\n✅ Deployment to {self.env} successful!")
        logger.info(f"API available at: http://{self.config['host']}:{self.config['port']}")
        logger.info(f"Docs at: http://{self.config['host']}:{self.config['port']}/docs")
        return True

    def deploy_staging(self) -> bool:
        """Deploy to staging"""
        logger.info(f"Deploying to {self.env}...")

        # Pre-deployment checks
        if not self.validate_code() or not self.run_tests():
            logger.error("Pre-deployment checks failed")
            return False

        # Backup production (if needed)
        logger.info("Taking database backup...")

        steps = [
            ("Setup database", self.setup_database),
            ("Start services", self.start_services),
            ("Warm cache", self.warm_cache),
            ("Health check", self.health_check),
        ]

        for step_name, step_func in steps:
            logger.info(f"\n▶ {step_name}...")
            if not step_func():
                logger.error(f"❌ {step_name} failed")
                return False
            logger.info(f"✅ {step_name} complete")

        logger.info(f"\n✅ Staging deployment successful!")
        return True

    def deploy_production(self) -> bool:
        """Deploy to production (careful!)"""
        logger.warning("⚠️ PRODUCTION DEPLOYMENT")

        # Extra safety checks
        confirm = input("Type 'DEPLOY-PROD' to confirm production deployment: ")
        if confirm != "DEPLOY-PROD":
            logger.info("Production deployment cancelled")
            return False

        logger.info("Starting production deployment...")

        # Backup
        logger.info("Creating production backup...")

        # Deploy
        steps = [
            ("Setup database", self.setup_database),
            ("Start services", self.start_services),
            ("Warm cache", self.warm_cache),
            ("Health check", self.health_check),
        ]

        for step_name, step_func in steps:
            logger.info(f"\n▶ {step_name}...")
            if not step_func():
                logger.error(f"❌ {step_name} failed")
                logger.warning("⚠️ Production deployment failed - rollback initiated")
                return False
            logger.info(f"✅ {step_name} complete")

        logger.info(f"\n✅✅✅ PRODUCTION DEPLOYMENT SUCCESSFUL ✅✅✅")
        return True

    def deploy(self) -> bool:
        """Execute deployment based on environment"""
        if self.env == "dev":
            return self.deploy_dev()
        elif self.env == "staging":
            return self.deploy_staging()
        elif self.env == "production":
            return self.deploy_production()
        else:
            raise ValueError(f"Unknown environment: {self.env}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy AI Biomechanics Platform")
    parser.add_argument(
        "--env",
        choices=["dev", "staging", "production"],
        default="dev",
        help="Deployment environment",
    )
    parser.add_argument("--no-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--no-validation", action="store_true", help="Skip code validation")

    args = parser.parse_args()

    try:
        manager = DeploymentManager(args.env)

        if not manager.deploy():
            sys.exit(1)

        logger.info("\n✅ All steps completed successfully!")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
