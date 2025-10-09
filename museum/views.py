from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from game.models import Team, Player  
from comms.models import Message
import random

def _player(request, team):
    pid = request.session.get("player_id")
    return Player.objects.filter(id=pid, team=team).first()

def _stable_shuffle(seq, seed):
    rng = random.Random(seed)
    items = list(seq)
    rng.shuffle(items)
    return items

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
    "A": ["🙂", "🔍", "🖼️"],
    "B": ["🌌", "✨", "🌙"],
    "C": ["🗿", "💪", "🪨"],
    "D": ["🌊", "⛵", "🗻"],
    "E": ["🕰️", "🫠", "🖼️"],
    "F": ["👧", "💎", "🧕"],
}

EXPECTED = {
    "A": "joconde",
    "B": "nuit-etoilee",
    "C": "david",
    "D": "vague-kanagawa",
    "E": "montres-molles",
    "F": "fille-perle",
}

# Version avec images plein format en debrief
ARTWORKS = [
    {"slug": "joconde",        "title": "La Joconde (Leonardo da Vinci)",               "img": "museum/joconde.png",        "img_full": "museum/full/joconde.png"},
    {"slug": "nuit-etoilee",   "title": "La Nuit étoilée (Vincent van Gogh)",           "img": "museum/nuit-etoilee.png",    "img_full": "museum/full/nuit-etoilee.png"},
    {"slug": "david",          "title": "David (Michel-Ange)",                           "img": "museum/david.png",           "img_full": "museum/full/david.png"},
    {"slug": "vague-kanagawa", "title": "La Grande Vague de Kanagawa (Hokusai)",        "img": "museum/vague-kanagawa.png",  "img_full": "museum/full/vague-kanagawa.png"},
    {"slug": "montres-molles", "title": "La Persistance de la mémoire (Salvador Dalí)", "img": "museum/montres-molles.png",  "img_full": "museum/full/montres-molles.png"},
    {"slug": "fille-perle",    "title": "La Jeune Fille à la perle (Johannes Vermeer)", "img": "museum/fille-perle.png",     "img_full": "museum/full/fille-perle.png"},
]

# Fiches pédagogiques (slug → infos)
ART_INFO = {
    "joconde": {
        "title": "La Joconde",
        "artist": "Leonardo da Vinci",
        "year": "c. 1503–1506",
        "country": "Italie",
        "note": "Portrait célèbre pour son sourire ‘énigmatique’ et l’usage du sfumato (dégradés doux)."
    },
    "nuit-etoilee": {
        "title": "La Nuit étoilée",
        "artist": "Vincent van Gogh",
        "year": "1889",
        "country": "Pays-Bas / France (Saint-Rémy)",
        "note": "Ciel tourbillonnant, couleurs intenses : une vision émotionnelle plus que réaliste."
    },
    "david": {
        "title": "David",
        "artist": "Michel-Ange",
        "year": "1501–1504",
        "country": "Italie",
        "note": "Sculpture en marbre de la Renaissance : idéal du corps humain et maîtrise anatomique."
    },
    "vague-kanagawa": {
        "title": "La Grande Vague de Kanagawa",
        "artist": "Katsushika Hokusai",
        "year": "c. 1831",
        "country": "Japon",
        "note": "Estampe ukiyo-e : composition dynamique et perspective influençant l’art en Europe."
    },
    "montres-molles": {
        "title": "La Persistance de la mémoire",
        "artist": "Salvador Dalí",
        "year": "1931",
        "country": "Espagne / France",
        "note": "Montres ‘molles’ : le temps devient subjectif, thème central du surréalisme."
    },
    "fille-perle": {
        "title": "La Jeune Fille à la perle",
        "artist": "Johannes Vermeer",
        "year": "c. 1665",
        "country": "Pays-Bas",
        "note": "‘Tronie’ (étude de visage) : lumière douce et perle iconique sur fond sombre."
    },
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
                # Progression + flag résolu
                team.current_order += 1
                team.museum_solved = True           # ✅ marque l’épreuve comme réussie
                team.save(update_fields=["current_order", "museum_solved"])

                # Message système
                Message.objects.create(team=team, player=None,
                                       text="🎉 Épreuve du Musée réussie !")
            else:
                team.score = max(0, team.score - 1)
                team.save(update_fields=["score"])
                feedback = "Ce n’est pas la bonne association. Discutez au chat et réessayez !"

    # ======= ORDRES DÉTERMINISTES PAR ÉQUIPE =======
    art_order = _stable_shuffle(list(range(len(ARTWORKS))), f"{team.uuid}-ART")
    emo_order = _stable_shuffle(list(EMOJI_SETS.keys()), f"{team.uuid}-EMO")

    artworks_display = []
    for i, art_idx in enumerate(art_order):
        art = ARTWORKS[art_idx]
        artworks_display.append({
            "slug": art["slug"],
            "img":  art["img"],
            "label": f"Œuvre {i+1}",
        })

    emoji_list = [{"key": k, "emojis": EMOJI_SETS[k]} for k in emo_order]

    next_ok = reverse("museum_debrief", args=[team.uuid])  # ← destination après succès

    base_ctx = {
        "team": team,
        "player": player,
        "feedback": feedback,
        "success": success,
        "next_url": next_ok,
        "artworks": artworks_display,
    }

    if player.role == "A":
        ctx = {**base_ctx, "role": "A", "emoji_list": None}
    else:
        ctx = {**base_ctx, "role": "B", "emoji_list": emoji_list}

    return render(request, "museum/puzzle.html", ctx)

def museum_debrief(request, team_uuid):
    team = get_object_or_404(Team, uuid=team_uuid)
    player = _player(request, team)
    if not player:
        return redirect("start")

    items = []
    for art in ARTWORKS:
        slug = art["slug"]
        info = ART_INFO[slug]
        items.append({
            "img_full": art.get("img_full", art["img"]),
            "title": info["title"],
            "artist": info["artist"],
            "year": info["year"],
            "country": info["country"],
            "note": info["note"],
        })

    return render(request, "museum/debrief.html", {
        "team": team,
        "player": player,
        "items": items,
    })
