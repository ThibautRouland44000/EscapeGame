from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from game.models import Team, Player     
from comms.models import Message             

def _player(request, team):
    pid = request.session.get("player_id")
    return Player.objects.filter(id=pid, team=team).first()

# état “scène” fixe pour la démo
SCENE = {
    "season": "printemps",
    "bulbs": 4,
    "label": "feuille",
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
        try:
            shower = int(request.POST.get("shower") or 10)        # minutes
        except (TypeError, ValueError):
            shower = 10
        light = (request.POST.get("light") or "moyenne").lower()  # "basse"/"moyenne"/"forte"

        # température AC si présente
        try:
            ac_temp = int(request.POST.get("ac_temp")) if request.POST.get("ac_temp") else None
        except (TypeError, ValueError):
            ac_temp = None

        # Règles de réussite
        ok_ac     = (ac == "on" and ac_temp == 23)
        ok_shower = (shower <= 5)
        ok_light  = (light == "basse")

        if ok_ac and ok_shower and ok_light:
            success = True
            team.current_order += 1
            team.hotel_solved = True            # ✅ flag réussite
            team.save(update_fields=["current_order", "hotel_solved"])

            Message.objects.create(
                team=team, player=None,
                text="🛏️ Épreuve Chambre réussie !"
            )
        else:
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
