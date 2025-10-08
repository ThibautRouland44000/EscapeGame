from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from game.models import Team, Player, TeamCode
from comms.models import Message
from game.views import PUZZLES

import json

def _player(request, team):
    pid = request.session.get("player_id")
    return Player.objects.filter(id=pid, team=team).first()

# --- Données de la carte ---
# Positions approximatives (en %) sur un fond de carte Europe (image fixe)
CITIES = {
    "LON":{"name":"Londres","x":35.0,"y":53.0},
    "PAR":{"name":"Paris","x":38.0,"y":65.0},
    "BRU":{"name":"Bruxelles","x":42.0,"y":57.0},
    "AMS":{"name":"Amsterdam","x":45,"y":53},
    "FRA":{"name":"Francfort","x":50,"y":58},
    "HAM":{"name":"Hambourg","x":50,"y":50},
    "BER":{"name":"Berlin","x":55,"y":58},
    "CPH":{"name":"Copenhague","x":53,"y":45},
    "STO":{"name":"Stockholm","x":60,"y":38},
    "PRA":{"name":"Prague","x":60.0,"y":60.0},
    "ZUR":{"name":"Zurich","x":46.0,"y":71.0},
    "MIL":{"name":"Milan","x":50.0,"y":75.0},
    "VEN":{"name":"Venise","x":50,"y":78},
    "BCN":{"name":"Barcelone","x":25,"y":80.0},
    "MAD":{"name":"Madrid","x":25,"y":86},
    "LIS":{"name":"Lisbonne","x":16,"y":78.0},
    "WAR":{"name":"Varsovie","x":68.0,"y":55.0},
}

# Liaisons ferroviaires (symétriques) avec "co2" = coût unitaire (points/eq.CO₂)
# NB: valeurs pédagogiques (pas des chiffres officiels).
ROUTES = {
    tuple(sorted(("LON","PAR"))): 12,
    tuple(sorted(("LON","BRU"))):  8,
    tuple(sorted(("BRU","AMS"))):  6,
    tuple(sorted(("AMS","FRA"))):  8,
    tuple(sorted(("FRA","BER"))): 12,
    tuple(sorted(("BER","HAM"))):  5,
    tuple(sorted(("HAM","CPH"))):  7,
    tuple(sorted(("CPH","STO"))): 10,
    tuple(sorted(("BER","PRA"))):  7,
    tuple(sorted(("PRA","VIE"))):  6,
    tuple(sorted(("VIE","BUD"))):  5,
    tuple(sorted(("VIE","MUN"))):  7,
    tuple(sorted(("MUN","ZUR"))):  5,
    tuple(sorted(("ZUR","MIL"))):  6,
    tuple(sorted(("MIL","VEN"))):  5,
    tuple(sorted(("VEN","ROM"))): 10,
    tuple(sorted(("PAR","BRU"))):  5,
    tuple(sorted(("PAR","FRA"))):  7,
    tuple(sorted(("PAR","BCN"))): 11,
    tuple(sorted(("BCN","MAD"))):  7,
    tuple(sorted(("MAD","LIS"))):  6,
    tuple(sorted(("PRA","WAR"))):  8,
    tuple(sorted(("WAR","BER"))):  8,
}

BUDGET      = 50   # plafond CO₂ total
MIN_CITIES  = 6     # au moins 6 villes visitées (donc >=5 trajets)

def _edge_cost(a, b):
    return ROUTES.get(tuple(sorted((a, b))))

def _total_cost(seq):
    """Calcule le coût total d'une séquence de villes (ex: ['PAR','BRU','AMS'])."""
    total = 0
    for i in range(len(seq)-1):
        c = _edge_cost(seq[i], seq[i+1])
        if c is None:
            return None  # liaison inexistante
        total += c
    return total

@require_http_methods(["GET", "POST"])
def rail_puzzle(request, team_uuid):
    team = get_object_or_404(Team, uuid=team_uuid)
    player = Player.objects.filter(id=request.session.get("player_id"), team=team).first()
    if not player:
        return redirect("start")

    success = False
    feedback = None

    if request.method == "POST" and player.role == "B":
        raw = (request.POST.get("itinerary") or "").strip()
        # format attendu: "PAR,BRU,AMS,..." (codes)
        seq = [s for s in raw.split(",") if s]
        # Vérifs
        if len(set(seq)) < MIN_CITIES:
            feedback = f"Trajet invalide : au moins {MIN_CITIES} villes distinctes."
        else:
            total = _total_cost(seq)
            if total is None:
                feedback = "Trajet invalide : liaison inexistante dans l’itinéraire."
            elif total > BUDGET:
                feedback = f"Budget CO₂ dépassé ({total} > {BUDGET})."
            else:
                # Succès
                success = True
                team.current_order += 1
                team.save(update_fields=["current_order"])

                try:
                    RAIL_CODE = next(p["code"] for p in PUZZLES if p["slug"] == "rail")
                except StopIteration:
                    RAIL_CODE = "RAIL2025"

                TeamCode.objects.get_or_create(team=team, puzzle_slug="rail",
                                               defaults={"code": RAIL_CODE})
                Message.objects.create(
                    team=team, player=None,
                    text=f"🚄 Épreuve Rail réussie ! 🔐 Code obtenu : {RAIL_CODE}"
                )

    # Prépare les données pour le template
    cities_list = [{"code":k, **v} for k,v in CITIES.items()]
    edges_list  = [{"a":a, "b":b, "co2":co2} for (a,b),co2 in ROUTES.items()]

    next_url = reverse("lobby", args=[team.uuid])

    ctx = {
        "team": team,
        "player": player,
        "role": "A" if player.role == "A" else "B",
        "success": success,
        "feedback": feedback,
        "next_url": next_url,
        "budget": BUDGET,
        "min_cities": MIN_CITIES,
        "cities": json.dumps(cities_list),
        "edges": json.dumps(edges_list),
    }
    return render(request, "rail/rail.html", ctx)
