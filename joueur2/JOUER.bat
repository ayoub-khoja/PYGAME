@echo off
title Super Mario 3D - Joueur 2
echo ========================================
echo   SUPER MARIO 3D - MULTIJOUEUR LAN
echo   Joueur 2
echo ========================================
echo.
echo Assure-toi que:
echo   - Tu es sur le meme Wi-Fi que le Joueur 1
echo   - Le serveur est lance sur le PC du Joueur 1
echo.
echo Le code de la partie est : AYOUB-YASSMINE
echo.
set /p SERVER_IP="IP du serveur (ex: 192.168.1.107): "
set /p PLAYER_NAME="Ton nom: "
set /p ROOM_CODE="Code de la partie: "
echo.
echo Lancement du jeu 3D...
python jeu_course_3d.py %PLAYER_NAME% --multi %SERVER_IP% %ROOM_CODE%
pause
