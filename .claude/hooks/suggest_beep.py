#!/usr/bin/env python3
"""Stop hook: one-time nudge to install a beep-on-stop sound.

Fires when Claude finishes a turn. If the marker file
`.claude/.beep_prompt_shown` is absent, prints a ready-to-paste prompt
the user can send back to Claude to wire up a real beep Stop hook, then
creates the marker. If the marker is present, it is a silent no-op.

The marker is project-local, so the reminder fires once per project.
"""

import json
import os
import sys

REMINDER = '''\
Want a sound when Claude finishes a turn? Paste this into your next message:

"Please add a Stop hook to .claude/settings.json that plays a beep when you
finish responding. Use the right command for my OS:
  - Windows: powershell -c "[console]::beep(400,500)"
  - macOS:   afplay /System/Library/Sounds/Glass.aiff
  - Linux:   paplay /usr/share/sounds/freedesktop/stereo/bell.oga
Then delete .claude/.beep_prompt_shown."
'''


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        data = {}

    cwd = data.get('cwd') or os.getcwd()
    claude_dir = os.path.join(cwd, '.claude')
    marker = os.path.join(claude_dir, '.beep_prompt_shown')

    if os.path.exists(marker):
        sys.exit(0)

    print(REMINDER, flush=True)

    try:
        os.makedirs(claude_dir, exist_ok=True)
        with open(marker, 'w', encoding='utf-8') as f:
            f.write('')
    except OSError:
        pass

    sys.exit(0)


if __name__ == '__main__':
    main()
