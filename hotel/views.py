from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from game.models import Team, Player, TeamCode
from comms.models import Message
from game.views import PUZZLES

def _player(request, team):
    pid = request.session.get("player_id")
    return Player.objects.filter(id=pid, team=team).first()

# état “scène” fixe pour la démo (cohérent avec les règles de succès)
SCENE = {
    "season": "printemps",   # printemps → clim/chauffage OFF (manuel)
    "bulbs": 4,              # 3+ = basse conso (manuel)
    "label": "feuille",      # feuille verte → < 5 min
    "mirror": "rectangulaire",
    "faucet": "bleu",
}

@require_http_methods(["GET", "POST"])
def room_puzzle(request, team_uuid):
    team = get_object_or_404(Team, uuid=team_uuid)
    player = _player(request, team)
    if not player:
        return redirect("start")

    feedback = None
    success = False

    if request.method == "POST" and player.role == "A":
        ac = (request.POST.get("ac") or "off").lower()            # "on" / "off"
        shower = int(request.POST.get("shower") or 10)            # minutes
        light = (request.POST.get("light") or "moyenne").lower()  # "basse"/"moyenne"/"forte"

        # température AC si présente
        try:
            ac_temp = int(request.POST.get("ac_temp")) if request.POST.get("ac_temp") else None
        except (TypeError, ValueError):
            ac_temp = None

        # Nouvelles règles de réussite
        ok_ac     = (ac == "on" and ac_temp == 23)
        ok_shower = (shower <= 5)
        ok_light  = (light == "basse")

        if ok_ac and ok_shower and ok_light:
            success = True
            team.current_order += 1
            team.save(update_fields=["current_order"])

            HOTEL_CODE = next(p["code"] for p in PUZZLES if p["slug"] == "hotel")
            TeamCode.objects.get_or_create(
                team=team, puzzle_slug="hotel", defaults={"code": HOTEL_CODE}
            )
            Message.objects.create(
                team=team, player=None,
                text=f"🛏️ Épreuve Chambre réussie ! 🔐 Code obtenu : {HOTEL_CODE}"
            )
        else:
            # Message unique, quel que soit l'erreur
            feedback = "Les réglages de la chambre d’hôtel sont incorrects."

    next_url = reverse("lobby", args=[team.uuid])
    ctx = {
        "team": team,
        "player": player,
        "scene": SCENE,
        "success": success,
        "feedback": feedback,
        "next_url": next_url,
        "role": "A" if player.role == "A" else "B",
    }
    return render(request, "hotel/room.html", ctx)
