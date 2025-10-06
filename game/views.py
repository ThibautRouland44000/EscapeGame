from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Team, Player

def _player(request, team):
    pid = request.session.get("player_id")
    return Player.objects.filter(id=pid, team=team).first()

def start(request):
    return render(request, "game/start_team.html")

@require_POST
def create_team(request):
    name = (request.POST.get("player_name") or "Alex").strip()
    team = Team.objects.create()
    alex = Player.objects.create(team=team, name=name, role="A", is_host=True)
    noa  = Player.objects.create(team=team, name="Noa", role="B")
    request.session["player_id"] = alex.id
    return redirect("lobby", team_uuid=team.uuid)

@require_POST
def join_team(request):
    code = (request.POST.get("code") or "").strip().upper()
    name = (request.POST.get("player_name") or "Noa").strip()
    team = get_object_or_404(Team, code=code)
    p = team.players.filter(role="B").first() or team.players.first()
    p.name = name
    p.save(update_fields=["name"])
    request.session["player_id"] = p.id
    return redirect("lobby", team_uuid=team.uuid)

def lobby(request, team_uuid):
    team = get_object_or_404(Team, uuid=team_uuid)
    player = _player(request, team)
    if not player:
        return redirect("start")
    return render(request, "game/lobby.html", {"team": team, "player": player})
