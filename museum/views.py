# museum/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from game.models import Team, Player
from comms.models import Message

def _player(request, team):
    pid = request.session.get("player_id")
    return Player.objects.filter(id=pid, team=team).first()

# --- DATASET FIXE (6 œuvres : peintures + David) ---
ARTWORKS = [
    {"slug": "joconde",        "title": "La Joconde (Leonardo da Vinci)",               "img": "museum/joconde.png"},
    {"slug": "nuit-etoilee",   "title": "La Nuit étoilée (Vincent van Gogh)",           "img": "museum/nuit-etoilee.png"},
    {"slug": "david",          "title": "David (Michel-Ange)",                           "img": "museum/david.png"},
    {"slug": "vague-kanagawa", "title": "La Grande Vague de Kanagawa (Hokusai)",        "img": "museum/vague-kanagawa.png"},
    {"slug": "montres-molles", "title": "La Persistance de la mémoire (Salvador Dalí)", "img": "museum/montres-molles.png"},
    {"slug": "fille-perle",    "title": "La Jeune Fille à la perle (Johannes Vermeer)", "img": "museum/fille-perle.png"},
]

EMOJI_SETS = {
    "A": ["🙂", "🔍", "🖼️"],   # Joconde — sourire énigmatique / chef-d’œuvre
    "B": ["🌌", "✨", "🌙"],   # Nuit étoilée — ciel nocturne
    "C": ["🗿", "💪", "🪨"],   # David — statue / force / marbre
    "D": ["🌊", "⛵", "🗻"],   # Grande Vague — vague / bateaux / Fuji
    "E": ["🕰️", "🫠", "🖼️"],  # Montres molles — horloges qui fondent
    "F": ["👧", "💎", "🧕"],   # Fille à la perle — portrait / perle / turban
}

EXPECTED = {
    "A": "joconde",
    "B": "nuit-etoilee",
    "C": "david",
    "D": "vague-kanagawa",
    "E": "montres-molles",
    "F": "fille-perle",
}

@require_http_methods(["GET","POST"])
def museum_puzzle(request, team_uuid):
    team = get_object_or_404(Team, uuid=team_uuid)
    player = _player(request, team)
    if not player:
        return redirect("start")

    feedback = None
    success = False  # flag pour l’overlay

    if request.method == "POST" and player.role == "B":
        # B envoie un mapping pour A..F → slug d’œuvre
        answers = {
            key: (request.POST.get(f"map_{key}") or "").strip()
            for key in EMOJI_SETS.keys()
        }
        # check complet
        if any(not v for v in answers.values()):
            feedback = "Il manque des associations, complète tout 🙂"
        else:
            if answers == EXPECTED:
                success = True
                # Progression + lettre (ex: “O”)
                team.current_order += 1
                if "O" not in (team.letters or ""):
                    team.letters += "O"
                team.save(update_fields=["current_order","letters"])

                # Message “Système” dans le chat visible par les 2 joueurs
                Message.objects.create(team=team, player=None,
                                       text="🎉 Épreuve du Musée réussie !")

                # Pas de redirect immédiat : l’overlay s’affiche dans le template
            else:
                team.score = max(0, team.score - 1)
                team.save(update_fields=["score"])
                feedback = "Ce n’est pas la bonne association. Discutez au chat et réessayez !"

    # Contexte selon rôle
    base_ctx = {
        "team": team,
        "player": player,
        "feedback": feedback,
        "success": success,
        "next_url": reverse("lobby", args=[team.uuid]),
    }
    if player.role == "A":
        ctx = {**base_ctx, "role": "A", "artworks": ARTWORKS, "emoji_sets": None}
    else:
        ctx = {**base_ctx, "role": "B", "artworks": ARTWORKS, "emoji_sets": EMOJI_SETS}

    return render(request, "museum/puzzle.html", ctx)
