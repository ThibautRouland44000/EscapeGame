# Office du Tourisme — L’Arnaque du Siècle (Frontend)

React + TypeScript + Vite + Tailwind (CDN) with BroadcastChannel simulating Socket.io between tabs.

## Dev

1) Install deps:

```
npm i
```

2) Start dev server:

```
npm run dev
```

3) Open two tabs:
- Tab 1: http://localhost:5173/?as=A
- Tab 2: http://localhost:5173/?as=B

Interact:
- B scanne des URLs et envoie des indices (boutons ou chat)
- Dès qu’un indice arrive, A peut “🚨 Bloquer ce site” (bonne réponse: citypass)

Assets placeholders expected at dev root:
- /affiche_visite360.png
- /affiche_citypass_superdeal.png
- /affiche_musee_croisiere.png

Drop images in frontend/office/public/ or use absolute URLs.


