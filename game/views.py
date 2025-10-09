# game/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

from .models import Team, Player  # ✅ plus de TeamCode ici

PUZZLES = [
    {"slug": "museum", "title": "Musée des œuvres"},
    {"slug": "hotel",  "title": "Chambre d'hôtel éco"},
    {"slug": "rail",   "title": "Tour d’Europe éco"},
]

def _player(request, team):
    pid = request.session.get("player_id")
    return Player.objects.filter(id=pid, team=team).first()

def start(request):
    return render(request, "game/start_team.html")

@require_POST
def create_team(request):
    name = (request.POST.get("player_name") or "Alex").strip()
    now = timezone.now()
    team = Team.objects.create(started_at=now, deadline_at=now + timedelta(minutes=10))
    alex = Player.objects.create(team=team, name=name, role="A", is_host=True)
    noa  = Player.objects.create(team=team, name="Noa", role="B")
    request.session["player_id"] = alex.id
    return redirect("lobby", team_uuid=team.uuid)

@require_POST
def join_team(request):
    code = (request.POST.get("code") or "").strip().upper()
    name = (request.POST.get("player_name") or "Noa").strip()
    team = get_object_or_404(Team, code=code)
    if not team.started_at or not team.deadline_at:
        now = timezone.now()
        team.started_at = now
        team.deadline_at = now + timedelta(minutes=10)
        team.save(update_fields=["started_at", "deadline_at"])
    p = team.players.filter(role="B").first() or team.players.first()
    p.name = name
    p.save(update_fields=["name"])
    request.session["player_id"] = p.id
    return redirect("lobby", team_uuid=team.uuid)

def lobby(request, team_uuid):
    team = get_object_or_404(Team, uuid=team_uuid)
    if not team.started_at or not team.deadline_at:
        now = timezone.now()
        team.started_at = now
        team.deadline_at = now + timedelta(minutes=10)
        team.save(update_fields=["started_at", "deadline_at"])

    player = _player(request, team)
    if not player:
        return redirect("start")

    # ✅ quelles épreuves sont réussies ? via flags
    solved_slugs = set()
    if team.museum_solved: solved_slugs.add("museum")
    if team.hotel_solved:  solved_slugs.add("hotel")
    if team.rail_solved:   solved_slugs.add("rail")

    puzzles = []
    for p in PUZZLES:
        if p["slug"] == "museum":
            url = reverse("museum_puzzle", args=[team.uuid]); enabled = True
        elif p["slug"] == "hotel":
            url = reverse("hotel_room", args=[team.uuid]); enabled = True
        elif p["slug"] == "rail":
            url = reverse("rail_puzzle", args=[team.uuid]); enabled = True
        else:
            url = "#"; enabled = False

        puzzles.append({
            "slug": p["slug"],
            "title": p["title"],
            "url": url,
            "enabled": enabled,
            "solved": (p["slug"] in solved_slugs),
        })

    # ✅ Indices affichés/débloqués selon les flags
    hints = [
        {
            "num": 1, "slug": "museum",
            "title": "Indice 1 — Mode d’emploi",
            "text": "Dans ce jeu, un chiffre peut cacher un autre.\nSi tu vois un nombre à deux chiffres, additionne-les pour n’en garder qu’un seul.",
            "enabled": "museum" in solved_slugs,
        },
        {
            "num": 2, "slug": "hotel",
            "title": "Indice 2 — Les trois nombres",
            "text": "« Nombre de côtés d’un triangle × 3 »\n« Nombre de doigts d’une main + 12 »\n« Nombre de minutes dans une heure ÷ 10 »",
            "enabled": "hotel" in solved_slugs,
        },
        {
            "num": 3, "slug": "rail",
            "title": "Indice 3 — L’ordre secret",
            "text": "Le chiffre le plus grand vient en premier,\nle plus petit à la suite du premier et le reste a la suite.",
            "enabled": "rail" in solved_slugs,
        },
    ]

    return render(request, "game/lobby.html", {
        "team": team,
        "player": player,
        "puzzles": puzzles,
        "hints": hints,
    })

@require_POST
def lock_validate_codes(request, team_uuid):
    """
    Seul le code final '968' ouvre le coffre (peu importe les épreuves).
    """
    team = get_object_or_404(Team, uuid=team_uuid)
    player = _player(request, team)
    if not player:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)

    final_code = (request.POST.get("final_code") or "").strip()
    if final_code == "968":
        if not team.finished_at:
            team.finished_at = timezone.now()
            team.save(update_fields=["finished_at"])
        from comms.models import Message
        Message.objects.create(team=team, player=None, text="🗝️ Coffre ouvert ! Bravo, vous avez trouvé 968.")
        return JsonResponse({"ok": True, "opened": True})
    else:
        return JsonResponse({"ok": True, "opened": False})
