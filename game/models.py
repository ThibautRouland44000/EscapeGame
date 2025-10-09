# game/models.py
from django.db import models
from django.utils import timezone
import uuid, random

def short_code(n=6):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(n))

class Team(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    code = models.CharField(max_length=8, unique=True, default=short_code)

    started_at = models.DateTimeField(blank=True, null=True)
    deadline_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    current_order = models.PositiveIntegerField(default=1)
    score = models.IntegerField(default=100)
    letters = models.CharField(max_length=10, default="")
    
    museum_solved = models.BooleanField(default=False)
    hotel_solved  = models.BooleanField(default=False)
    rail_solved   = models.BooleanField(default=False)

class Player(models.Model):
    ROLES = [("A","Alex"), ("B","Noa")]
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=80)
    role = models.CharField(max_length=1, choices=ROLES)
    is_host = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)

# Tu peux garder ce modèle si des migrations/anciens jeux l’utilisent,
# mais le gameplay actuel n’en dépend plus.
class TeamCode(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="codes")
    puzzle_slug = models.CharField(max_length=32)
    code = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("team", "puzzle_slug")
