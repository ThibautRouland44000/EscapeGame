# game/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Team, Player, TeamCode
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta  # ⬅️ utile pour le chrono

PUZZLES = [
    {"slug": "museum", "title": "Musée des œuvres", "code": "ARTE"},
    {"slug": "hotel",  "title": "Chambre d'hôtel éco", "code": "ECO"},
    {"slug": "rail",   "title": "Tour d’Europe éco",  "code": "RAIL"},
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
    # ⏱️ Démarre le compte à rebours de 10 min dès la création
    team = Team.objects.create(
        started_at=now,
        deadline_at=now + timedelta(minutes=10),
    )
    alex = Player.objects.create(team=team, name=name, role="A", is_host=True)
    noa  = Player.objects.create(team=team, name="Noa", role="B")
    request.session["player_id"] = alex.id
    return redirect("lobby", team_uuid=team.uuid)

@require_POST
def join_team(request):
    code = (request.POST.get("code") or "").strip().upper()
    name = (request.POST.get("player_name") or "Noa").strip()
    team = get_object_or_404(Team, code=code)

    # ⏱️ Sécurité : si, pour une raison quelconque, le timer n'existe pas, on l'initialise
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

    # ⏱️ Sécurité bis : s'assurer que le timer existe toujours
    if not team.started_at or not team.deadline_at:
        now = timezone.now()
        team.started_at = now
        team.deadline_at = now + timedelta(minutes=10)
        team.save(update_fields=["started_at", "deadline_at"])

    player = _player(request, team)
    if not player:
        return redirect("start")

    got_codes = {tc.puzzle_slug: tc.code for tc in TeamCode.objects.filter(team=team)}

    puzzles = []
    for p in PUZZLES:
        if p["slug"] == "museum":
            url = reverse("museum_puzzle", args=[team.uuid]); enabled = True
        elif p["slug"] == "hotel":
            url = reverse("hotel_room", args=[team.uuid]); enabled = True
        elif p["slug"] == "rail":
            url = reverse("rail_puzzle", args=[team.uuid]);  enabled = True
        else:
            url = "#"; enabled = False

        puzzles.append({
            "slug": p["slug"],
            "title": p["title"],
            "url": url,
            "enabled": enabled,
            "solved": (p["slug"] in got_codes),
        })

    need_count = len(PUZZLES)
    slots = list(range(need_count))
    found_codes = list(got_codes.values())

    return render(request, "game/lobby.html", {
        "team": team,                # ⬅️ important : le header lit team.deadline_at
        "player": player,
        "puzzles": puzzles,
        "need_count": need_count,
        "slots": slots,
        "found_codes": found_codes,
    })

@require_POST
def lock_check_code(request, team_uuid):
    team = get_object_or_404(Team, uuid=team_uuid)
    player = _player(request, team)
    if not player:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    code = (request.POST.get("code") or "").strip().upper()
    team_codes = set(TeamCode.objects.filter(team=team).values_list("code", flat=True))
    return JsonResponse({"ok": True, "match": code in team_codes})

@require_POST
def lock_validate_codes(request, team_uuid):
    team = get_object_or_404(Team, uuid=team_uuid)
    player = _player(request, team)
    if not player:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)

    # codes[] ou codes_csv
    raw = request.POST.getlist("codes")
    if not raw:
        raw = [c.strip() for c in (request.POST.get("codes_csv") or "").split(",") if c.strip()]
    entered = [c.upper() for c in raw if c.strip()]

    need = len(PUZZLES)
    if len(entered) != need:
        return JsonResponse({"ok": False, "error": "missing_or_extra", "need": need}, status=400)

    team_codes = set(TeamCode.objects.filter(team=team).values_list("code", flat=True))
    if len(team_codes) != need:
        return JsonResponse({"ok": False, "error": "not_all_solved"}, status=400)

    if set(entered) == team_codes:
        if not team.finished_at:
            team.finished_at = timezone.now()
            team.save(update_fields=["finished_at"])
        from comms.models import Message
        Message.objects.create(team=team, player=None, text="🗝️ Coffre ouvert ! Bravo, toutes les épreuves sont réussies.")
        return JsonResponse({"ok": True, "opened": True})
    else:
        return JsonResponse({"ok": True, "opened": False})
