# 🎮 Super Mario - Aventure Étoilée (Pygame Version)

Une version Pygame de l'écran d'accueil du jeu Super Mario - Aventure Étoilée.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.5+-green.svg)

## 📖 Description

Ce projet est une adaptation en Pygame de la page d'accueil HTML du jeu "Super Mario - Aventure Étoilée". Il comprend :

- 🎨 Un écran d'accueil avec fond animé
- 📝 Saisie du nom du joueur
- 🎵 Musique de fond
- 🎯 Description des 3 niveaux du jeu
- ⌨️ Instructions avec les touches directionnelles

## 🎯 Niveaux du jeu

| Niveau | Nom | Description |
|--------|-----|-------------|
| 1 | L'Explorer Normal | Récupérer les étoiles en évitant les bombes |
| 2 | L'Aventure en Mutation | La scène change dynamiquement avec de nouveaux obstacles |
| 3 | Le Défi Ultime | Le niveau le plus difficile avec plus de bombes |

## 🚀 Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes

1. **Cloner le dépôt** (ou télécharger les fichiers)
```bash
git clone https://github.com/ayoub-khoja/PYGAME.git
cd PYGAME/gamePygame
```

2. **Créer un environnement virtuel** (recommandé)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

## ▶️ Lancement

```bash
python main.py
```

## 🎮 Contrôles

| Touche | Action |
|--------|--------|
| ↑ | Déplacer vers le haut |
| ↓ | Déplacer vers le bas |
| ← | Déplacer vers la gauche |
| → | Déplacer vers la droite |
| Entrée | Valider le nom / Démarrer |

## 📁 Structure du projet

```
gamePygame/
├── main.py              # Fichier principal du jeu
├── requirements.txt     # Dépendances Python
├── README.md           # Documentation
└── assets/             # Ressources du jeu
    ├── background.webp # Image de fond
    ├── arrow.png       # Image des touches
    └── 02. Menu.mp3    # Musique de fond
```

## 🛠️ Technologies utilisées

- **Python 3** - Langage de programmation
- **Pygame** - Bibliothèque pour le développement de jeux

## 📝 Fonctionnalités

- [x] Écran d'accueil avec design fidèle à l'original
- [x] Champ de saisie pour le nom du joueur
- [x] Bouton "Démarrer le Jeu" interactif
- [x] Musique de fond en boucle
- [x] Affichage des instructions de jeu
- [x] Notifications toast animées
- [ ] Intégration avec le jeu principal (à venir)

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

Ce projet est sous licence ISC.

## 👤 Auteur

**Ayoub Khoja**

---

⭐ N'oubliez pas de mettre une étoile si ce projet vous a plu !
