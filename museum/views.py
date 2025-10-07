from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from game.models import Team, Player

def _player(request, team):
    pid = request.session.get("player_id")
    return Player.objects.filter(id=pid, team=team).first()

# --- DATASET FIXE (toujours les mêmes) ---
# 6 œuvres (slug, titre, fichier image dans static/museum/)
ARTWORKS = [
    {"slug": "joconde", "title": "La Joconde (Leonardo da Vinci)", "img": "museum/joconde.png"},
    {"slug": "nuit-etoilee", "title": "La Nuit étoilée (Van Gogh)", "img": "museum/nuit-etoilee.png"},
    {"slug": "david", "title": "David (Michel-Ange)", "img": "museum/david.png"},
    {"slug": "vague-kanagawa", "title": "La Grande Vague de Kanagawa (Hokusai)", "img": "museum/vague-kanagawa.png"},
    {"slug": "montres-molles", "title": "La Persistance de la mémoire (Dalí)", "img": "museum/montres-molles.png"},
    {"slug": "fille-perle", "title": "La Jeune Fille à la perle (Vermeer)", "img": "museum/fille-perle.png"},
]
# 6 listes d’emojis (toujours les mêmes) → à associer aux œuvres
# Clés A..F pour l’interface côté B
EMOJI_SETS = {
    "A": ["🙂", "🔍", "🖼️"],          # Joconde — sourire énigmatique / chef-d’œuvre
    "B": ["🌌", "✨", "🌙"],          # Nuit étoilée — ciel nocturne
    "C": ["🗿", "💪", "🪨"],          # David — statue / force / marbre
    "D": ["🌊", "⛵", "🗻"],          # Grande Vague — vague/bateaux/Fuji
    "E": ["🕰️", "🫠", "🖼️"],          # Montres molles — horloges qui fondent
    "F": ["👧", "💎", "🧕"],          # Fille à la perle — portrait/turban/boucle
}
# Mapping attendu EMO set -> slug œuvre
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
    ok = False

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
                ok = True
                # Avance la partie si tu veux chaîner les épreuves
                team.current_order += 1
                # Optionnel: ajouter une lettre “O” à “OUVRE” par exemple
                if "O" not in (team.letters or ""):
                    team.letters += "O"
                team.save(update_fields=["current_order","letters"])
                return redirect("lobby", team_uuid=team.uuid)
            else:
                team.score = max(0, team.score - 1)
                team.save(update_fields=["score"])
                feedback = "Ce n’est pas la bonne association. Discutez au chat et réessayez !"

    # Prépare l’affichage selon rôle
    if player.role == "A":
        context = {
            "role": "A",
            "artworks": ARTWORKS,  # A voit les 6 images (numérotées 1..6 visuellement)
            "emoji_sets": None,
            "feedback": feedback,
            "team": team,
            "player": player,
        }
    else:  # role B
        # B voit les 6 paquets d’emojis avec des select d’œuvre
        context = {
            "role": "B",
            "artworks": ARTWORKS,   # pour les options de select (titres)
            "emoji_sets": EMOJI_SETS,
            "feedback": feedback,
            "team": team,
            "player": player,
        }
    return render(request, "museum/puzzle.html", context)
