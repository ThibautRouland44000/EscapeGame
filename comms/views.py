from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from game.models import Team, Player
from .models import Message

def _player(request, team):
    pid = request.session.get("player_id")
    return Player.objects.filter(id=pid, team=team).first()

def fetch(request, team_uuid):
    team = get_object_or_404(Team, uuid=team_uuid)
    player = _player(request, team)
    if not player:
        return JsonResponse({"error":"unauthorized"}, status=403)
    since = int(request.GET.get("since", 0))
    msgs = team.messages.filter(id__gt=since).order_by("id")[:100]
    out = [{"id":m.id, "p":(m.player.name if m.player else "Système"), "t":m.text, "ts":m.created.isoformat()} for m in msgs]
    return JsonResponse({"messages": out})

@require_POST
def send(request, team_uuid):
    team = get_object_or_404(Team, uuid=team_uuid)
    player = _player(request, team)
    if not player:
        return JsonResponse({"error":"unauthorized"}, status=403)

    # rate-limit: 1 msg/s
    key = f"chat_rl_{player.id}"
    if cache.get(key):
        return JsonResponse({"ok": False, "error":"too_fast"}, status=429)
    cache.set(key, 1, timeout=1)

    txt = (request.POST.get("text") or "").strip()[:300]
    if not txt:
        return JsonResponse({"ok": False}, status=400)
    m = Message.objects.create(team=team, player=player, text=txt)
    return JsonResponse({"ok": True, "id": m.id})
