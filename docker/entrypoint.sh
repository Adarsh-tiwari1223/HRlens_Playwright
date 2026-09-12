#!/bin/bash
set -e

# ==============================================================================
# HRlens Automation Container Entrypoint
# Dynamically branches between CI/CD (headless) and Local (noVNC GUI streaming)
# ==============================================================================

IS_CI=false
if [ "${CI,,}" = "true" ] || [ "${GITHUB_ACTIONS,,}" = "true" ] || [ "${HEADLESS,,}" = "true" ]; then
    IS_CI=true
fi

if [ "$IS_CI" = "true" ]; then
    echo "-----------------------------------------------------------------"
    echo " [CI/CD MODE] Running Playwright in Headless mode (noVNC bypassed)"
    echo "-----------------------------------------------------------------"
    exec "$@"
fi

# ------------------------------------------------------------------------------
# LOCAL RUN: Initialize Xvfb, Fluxbox, x11vnc, and noVNC (port 6080)
# ------------------------------------------------------------------------------
echo "================================================================="
echo " [GUI MODE] Initializing Virtual Display & noVNC Web Stream"
echo "================================================================="

export DISPLAY=:99
export SCREEN_RESOLUTION=${SCREEN_RESOLUTION:-1920x1080x24}

# 1. Clean up any stale X locks
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 2>/dev/null || true

# 2. Start Xvfb Virtual Framebuffer
Xvfb :99 -screen 0 $SCREEN_RESOLUTION -ac -nolisten tcp &
XVFB_PID=$!

# Wait for X display to become ready
for i in $(seq 1 10); do
    if xdpyinfo -display :99 >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

# 3. Start lightweight window manager
fluxbox &
FLUXBOX_PID=$!

# 4. Start x11vnc server on port 5900
x11vnc -display :99 -forever -nopw -shared -rfbport 5900 -quiet &
X11VNC_PID=$!

# 5. Start noVNC websockify bridge on port 6080
websockify --web=/usr/share/novnc 6080 localhost:5900 >/dev/null 2>&1 &
WEBSOCK_PID=$!

echo "================================================================="
echo " 🌐 noVNC Live GUI Stream Ready!"
echo " 👉 Open in your browser: http://localhost:6080"
echo "================================================================="

# Trap termination signals to cleanly shut down daemons
cleanup() {
    kill $WEBSOCK_PID $X11VNC_PID $FLUXBOX_PID $XVFB_PID 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Run the test command
"$@"
EXIT_CODE=$?

cleanup
exit $EXIT_CODE
