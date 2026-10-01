#!/usr/bin/env bash
# Configure Ubuntu GNOME shortcut Super+Shift+J to launch Bro HUD in audio-only hands-free mode

set -e

SHORTCUT_NAME="Bro HUD Voice Mode"
SHORTCUT_CMD='xdg-open "http://127.0.0.1:8765/?mode=audio_only&greet=1&loop=1"'
SHORTCUT_BINDING="<Super><Shift>j"

echo "Configuring Ubuntu GNOME shortcut: $SHORTCUT_BINDING -> $SHORTCUT_NAME"

if ! command -v gsettings &>/dev/null; then
    echo "Warning: gsettings command not found. Skipping GNOME shortcut configuration."
    exit 0
fi

# Fetch current list of custom keybindings
CURRENT=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings 2>/dev/null || echo "@as []")

# Determine custom path
BASE_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/bro/"
SCHEMA="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$BASE_PATH"

# Set binding details
gsettings set "$SCHEMA" name "$SHORTCUT_NAME"
gsettings set "$SCHEMA" command "$SHORTCUT_CMD"
gsettings set "$SCHEMA" binding "$SHORTCUT_BINDING"

# Add to list if not already present
if [[ "$CURRENT" != *"$BASE_PATH"* ]]; then
    if [[ "$CURRENT" == "@as []" ]] || [[ "$CURRENT" == "[]" ]]; then
        NEW_LIST="['$BASE_PATH']"
    else
        # Strip trailing ']'
        TRIMMED="${CURRENT%]}"
        NEW_LIST="${TRIMMED}, '$BASE_PATH']"
    fi
    gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$NEW_LIST"
fi

echo "Successfully configured keybinding Super+Shift+J to open Bro HUD with auto-greeting and hands-free loop."
