from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from game.models import Team, Player


def _player(request, team):
    pid = request.session.get("player_id")
    return Player.objects.filter(id=pid, team=team).first()


POSTERS = [
    {"slug": "visite360", "title": "Visite 360° de la ville", "price": "15 €", "url": "visite360-ville.com", "img": "museum/joconde.png", "legit": True},
    {"slug": "citypass", "title": "Pass Luxe Tout Gratuit", "price": "2 €", "url": "citypass-superdeal.biz", "img": "museum/montres-molles.png", "legit": False},
    {"slug": "croisiere", "title": "Croisière Historique", "price": "18 €", "url": "musee-ville.fr", "img": "museum/vague-kanagawa.png", "legit": True},
]

HINTS_BY_STATUS = {
    "FAKE": [
        "Protocole suspect (HTTP)",
        "Domaine nouveau / suspect",
        "Nom proche du vrai site",
    ],
    "SECURE": [
        "HTTPS valide",
        "Design sobre et cohérent",
    ],
}

SECURE_REPORT = {
    "visite360-ville.com": "SECURE",
    "musee-ville.fr": "SECURE",
    "citypass-superdeal.biz": "FAKE",
}


@require_http_methods(["GET", "POST"])
def office_game(request, team_uuid):
    team = get_object_or_404(Team, uuid=team_uuid)
    player = _player(request, team)
    if not player:
        return redirect("start")

    # Chat + flow similar to museum: show chat on right via template include

    feedback = None
    scanned_host = None
    scanned_hints = None

    # Allow role override for demo/testing in a single browser (?as=A or ?as=B)
    as_param = (request.GET.get("as") or "").strip().upper()
    effective_role = as_param if as_param in {"A","B"} else player.role

    if request.method == "POST":
        if effective_role == "B":
            scanned_host = (request.POST.get("host") or "").strip().lower()
            status = SECURE_REPORT.get(scanned_host)
            if status:
                scanned_hints = HINTS_BY_STATUS[status]
            else:
                scanned_hints = ["Hôte inconnu — demande l’URL exacte à A"]
        else:  # A blocks
            block_slug = (request.POST.get("block_slug") or "").strip()
            selected = next((p for p in POSTERS if p["slug"] == block_slug), None)
            if not selected:
                feedback = "Choix invalide."
            else:
                if selected["legit"]:
                    team.score = max(0, team.score - 1)
                    team.save(update_fields=["score"])
                    feedback = "⛔ Site légitime bloqué ! Revérifiez les indices."
                else:
                    team.current_order += 1
                    team.save(update_fields=["current_order"])
                    return redirect("lobby", team_uuid=team.uuid)

    context = {
        "team": team,
        "player": player,
        "role": effective_role,
        "posters": POSTERS,
        "feedback": feedback,
        "scanned_host": scanned_host,
        "scanned_hints": scanned_hints,
    }
    return render(request, "office/game.html", context)


