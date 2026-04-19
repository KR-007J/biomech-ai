"""
TIER 6: Social Features & Gamification
Leaderboards, challenges, achievements, and social competition
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


class LeaderboardType(str, Enum):
    """Leaderboard types"""

    GLOBAL = "global"
    REGIONAL = "regional"
    FRIEND = "friend"
    TEAM = "team"


class ChallengeStatus(str, Enum):
    """Challenge statuses"""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class AchievementCategory(str, Enum):
    """Achievement categories"""

    STRENGTH = "strength"
    ENDURANCE = "endurance"
    CONSISTENCY = "consistency"
    FORM = "form"
    MILESTONE = "milestone"


@dataclass
class LeaderboardEntry:
    """Single leaderboard entry"""

    rank: int
    user_id: str
    username: str
    score: float
    metric: str
    period: str  # "daily", "weekly", "monthly", "all_time"
    avatar_url: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "rank": self.rank,
            "user_id": self.user_id,
            "username": self.username,
            "score": self.score,
            "metric": self.metric,
            "period": self.period,
        }


@dataclass
class Challenge:
    """User challenge/goal"""

    challenge_id: str
    user_id: str
    name: str
    description: str
    target_value: float
    current_value: float
    metric: str  # "reps", "weight", "duration", "form_score"
    status: ChallengeStatus
    created_at: datetime
    expires_at: datetime
    reward_points: int
    difficulty: str  # "easy", "medium", "hard"

    def progress_percent(self) -> float:
        if self.target_value == 0:
            return 0
        return min(100, (self.current_value / self.target_value) * 100)

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at and self.status != ChallengeStatus.COMPLETED

    def to_dict(self) -> Dict:
        return {
            "challenge_id": self.challenge_id,
            "name": self.name,
            "target": self.target_value,
            "current": self.current_value,
            "progress": self.progress_percent(),
            "status": self.status.value,
            "points": self.reward_points,
        }


@dataclass
class Achievement:
    """User achievement/badge"""

    achievement_id: str
    user_id: str
    name: str
    description: str
    category: AchievementCategory
    icon_url: str
    unlocked_at: datetime
    points_awarded: int
    rarity: str  # "common", "rare", "epic", "legendary"

    def to_dict(self) -> Dict:
        return {
            "achievement_id": self.achievement_id,
            "name": self.name,
            "category": self.category.value,
            "unlocked_at": self.unlocked_at.isoformat(),
            "points": self.points_awarded,
            "rarity": self.rarity,
        }


@dataclass
class UserProfile:
    """Enhanced user profile with social data"""

    user_id: str
    username: str
    level: int
    total_points: int
    friends: List[str] = field(default_factory=list)
    followers: List[str] = field(default_factory=list)
    following: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)  # achievement IDs
    bio: str = ""
    avatar_url: Optional[str] = None
    is_public: bool = True


# ============================================================================
# SOCIAL ENGINE
# ============================================================================


class SocialGamificationEngine:
    """
    Social features and gamification system
    """

    def __init__(self):
        self.users: Dict[str, UserProfile] = {}
        self.leaderboards: Dict[str, List[LeaderboardEntry]] = {}
        self.challenges: Dict[str, Challenge] = {}
        self.achievements: Dict[str, Achievement] = {}
        self.user_challenges: Dict[str, List[str]] = {}  # user_id -> challenge_ids
        self.user_achievements: Dict[str, List[str]] = {}  # user_id -> achievement_ids

        logger.info("Social gamification engine initialized")

    async def create_user_profile(self, user_id: str, username: str) -> Dict[str, Any]:
        """Create social profile for user"""
        try:
            profile = UserProfile(user_id=user_id, username=username, level=1, total_points=0)
            self.users[user_id] = profile
            self.user_challenges[user_id] = []
            self.user_achievements[user_id] = []

            logger.info(f"User profile created: {username}")

            return {"success": True, "user_id": user_id, "level": 1, "points": 0}
        except Exception as e:
            logger.error(f"Profile creation failed: {str(e)}")
            return {"error": str(e)}

    async def get_leaderboard(
        self,
        leaderboard_type: str = "global",
        metric: str = "total_reps",
        period: str = "weekly",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get leaderboard

        Args:
            leaderboard_type: Type of leaderboard
            metric: Metric to rank by
            period: Time period
            limit: Number of entries

        Returns:
            Leaderboard entries
        """
        try:
            leaderboard_key = f"{leaderboard_type}:{metric}:{period}"

            # In production, calculate from actual data
            entries = []
            for rank, (user_id, profile) in enumerate(self.users.items(), 1):
                if rank > limit:
                    break

                entry = LeaderboardEntry(
                    rank=rank,
                    user_id=user_id,
                    username=profile.username,
                    score=profile.total_points,
                    metric=metric,
                    period=period,
                    avatar_url=profile.avatar_url,
                )
                entries.append(entry)

            self.leaderboards[leaderboard_key] = entries

            return {
                "leaderboard_type": leaderboard_type,
                "metric": metric,
                "period": period,
                "entries": [e.to_dict() for e in entries],
                "entry_count": len(entries),
            }
        except Exception as e:
            logger.error(f"Leaderboard fetch failed: {str(e)}")
            return {"error": str(e)}

    async def create_challenge(
        self,
        user_id: str,
        name: str,
        target_value: float,
        metric: str,
        difficulty: str = "medium",
        duration_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Create challenge for user

        Args:
            user_id: User creating challenge
            name: Challenge name
            target_value: Target value to achieve
            metric: Metric type
            difficulty: Challenge difficulty
            duration_days: Challenge duration

        Returns:
            Challenge details
        """
        try:
            challenge_id = str(uuid.uuid4())

            # Points based on difficulty
            points = {"easy": 100, "medium": 250, "hard": 500}.get(difficulty, 250)

            challenge = Challenge(
                challenge_id=challenge_id,
                user_id=user_id,
                name=name,
                description=f"Reach {target_value} {metric}",
                target_value=target_value,
                current_value=0,
                metric=metric,
                status=ChallengeStatus.ACTIVE,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=duration_days),
                reward_points=points,
                difficulty=difficulty,
            )

            self.challenges[challenge_id] = challenge
            self.user_challenges[user_id].append(challenge_id)

            logger.info(f"Challenge created: {challenge_id} for user {user_id}")

            return {"success": True, "challenge": challenge.to_dict()}
        except Exception as e:
            logger.error(f"Challenge creation failed: {str(e)}")
            return {"error": str(e)}

    async def update_challenge_progress(self, challenge_id: str, value: float) -> Dict[str, Any]:
        """Update challenge progress"""
        try:
            challenge = self.challenges.get(challenge_id)
            if not challenge:
                return {"error": "Challenge not found"}

            challenge.current_value = value

            # Check if completed
            if challenge.current_value >= challenge.target_value:
                challenge.status = ChallengeStatus.COMPLETED

                # Award points
                user = self.users.get(challenge.user_id)
                if user:
                    user.total_points += challenge.reward_points

            elif challenge.is_expired():
                challenge.status = ChallengeStatus.EXPIRED

            return {
                "challenge": challenge.to_dict(),
                "completed": challenge.status == ChallengeStatus.COMPLETED,
            }
        except Exception as e:
            logger.error(f"Progress update failed: {str(e)}")
            return {"error": str(e)}

    async def unlock_achievement(
        self, user_id: str, category: str, name: str, description: str
    ) -> Dict[str, Any]:
        """
        Unlock achievement for user

        Args:
            user_id: User ID
            category: Achievement category
            name: Achievement name
            description: Achievement description

        Returns:
            Achievement details
        """
        try:
            achievement_id = str(uuid.uuid4())

            # Points and rarity based on category
            category_data = {
                AchievementCategory.STRENGTH: {"points": 50, "rarity": "common"},
                AchievementCategory.ENDURANCE: {"points": 75, "rarity": "rare"},
                AchievementCategory.CONSISTENCY: {"points": 100, "rarity": "epic"},
                AchievementCategory.FORM: {"points": 150, "rarity": "rare"},
                AchievementCategory.MILESTONE: {"points": 200, "rarity": "legendary"},
            }

            data = category_data.get(
                AchievementCategory(category), {"points": 50, "rarity": "common"}
            )

            achievement = Achievement(
                achievement_id=achievement_id,
                user_id=user_id,
                name=name,
                description=description,
                category=AchievementCategory(category),
                icon_url=f"/assets/achievements/{category}.png",
                unlocked_at=datetime.utcnow(),
                points_awarded=data["points"],
                rarity=data["rarity"],
            )

            self.achievements[achievement_id] = achievement
            self.user_achievements[user_id].append(achievement_id)

            # Award points
            user = self.users.get(user_id)
            if user:
                user.total_points += achievement.points_awarded
                user.achievements.append(achievement_id)

            logger.info(f"Achievement unlocked: {name} for user {user_id}")

            return {"success": True, "achievement": achievement.to_dict()}
        except Exception as e:
            logger.error(f"Achievement unlock failed: {str(e)}")
            return {"error": str(e)}

    async def add_friend(self, user_id: str, friend_id: str) -> Dict[str, bool]:
        """Add friend"""
        try:
            user = self.users.get(user_id)
            friend = self.users.get(friend_id)

            if not user or not friend:
                return {"success": False, "error": "User not found"}

            if friend_id not in user.friends:
                user.friends.append(friend_id)
                user.following.append(friend_id)

            if user_id not in friend.followers:
                friend.followers.append(user_id)

            logger.info(f"Friends added: {user_id} <-> {friend_id}")

            return {"success": True}
        except Exception as e:
            logger.error(f"Add friend failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user social profile"""
        try:
            user = self.users.get(user_id)
            if not user:
                return {"error": "User not found"}

            achievements = [
                self.achievements.get(aid).to_dict()
                for aid in user.achievements
                if aid in self.achievements
            ]

            return {
                "user_id": user_id,
                "username": user.username,
                "level": user.level,
                "total_points": user.total_points,
                "friends_count": len(user.friends),
                "followers_count": len(user.followers),
                "achievements_count": len(user.achievements),
                "achievements": achievements,
                "is_public": user.is_public,
            }
        except Exception as e:
            logger.error(f"Profile fetch failed: {str(e)}")
            return {"error": str(e)}

    async def get_user_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user dashboard"""
        try:
            user = self.users.get(user_id)
            if not user:
                return {"error": "User not found"}

            # Get active challenges
            active_challenges = [
                self.challenges.get(cid).to_dict()
                for cid in self.user_challenges.get(user_id, [])
                if cid in self.challenges and self.challenges[cid].status == ChallengeStatus.ACTIVE
            ]

            # Get rank
            leaderboard_key = "global:total_reps:weekly"
            leaderboard = self.leaderboards.get(leaderboard_key, [])
            rank = next((e.rank for e in leaderboard if e.user_id == user_id), None)

            return {
                "user_id": user_id,
                "username": user.username,
                "level": user.level,
                "total_points": user.total_points,
                "rank": rank,
                "active_challenges": active_challenges,
                "achievements_unlocked": len(user.achievements),
                "next_milestone": user.level * 1000,
                "progress_to_next_level": (user.total_points % 1000) / 10,
            }
        except Exception as e:
            logger.error(f"Dashboard fetch failed: {str(e)}")
            return {"error": str(e)}


logger.info("Social gamification engine module loaded - Tier 6 partial complete")
