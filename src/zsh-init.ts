export const ZSH_INIT_SCRIPT = `
# This widget re-defines what 'Enter' (accept-line) does.
shai_enter_to_expand() {

  # Check if the current line buffer starts with "shai "
  if [[ $BUFFER == shai\\ * ]]; then

    # It's a shai command. We want to *transform* it, not execute it yet.
    local prompt=\${BUFFER#shai }
    local original_buffer="$BUFFER"

    # Create a temp file to capture the command output
    local tmpfile=$(mktemp)

    # Run shai in the background, capturing stdout to temp file
    # stderr goes to /dev/tty so errors are visible
    (command shai "$prompt" > "$tmpfile" 2>/dev/tty) &|
    local shai_pid=$!

    # Wave spinner animation (rises and falls)
    local spin_idx=1

    # Hide cursor during animation
    printf "\\e[?25l" > /dev/tty

    # Ensure we always cleanup on exit (cursor restore and temp file deletion)
    trap 'printf "\\e[?25h" > /dev/tty; [[ -f "$tmpfile" ]] && rm -f "$tmpfile"' EXIT INT TERM

    # While shai is still running, show spinner
    while kill -0 $shai_pid 2>/dev/null; do
      # Wave pattern rising and falling
      case $spin_idx in
        1) BUFFER=" ▂▄▆█" ;;
        2) BUFFER=" ▃▅▇▓" ;;
        3) BUFFER=" ▄▆█▒" ;;
        4) BUFFER=" ▅▇▓░" ;;
        5) BUFFER=" ▆█▒░" ;;
        6) BUFFER=" ▇▓░▁" ;;
        7) BUFFER=" █▒░▂" ;;
        8) BUFFER=" ▓░▁▃" ;;
      esac
      zle redisplay

      # Move to next frame
      spin_idx=$((spin_idx + 1))
      if [[ $spin_idx -gt 8 ]]; then
        spin_idx=1
      fi

      # Animation delay (0.15 seconds for smoother wave)
      sleep 0.15
    done

    # Read the generated command
    local new_command=""
    if [[ -f "$tmpfile" ]]; then
      new_command=$(cat "$tmpfile")
    fi

    # Check if we got a command back and shai succeeded
    if [[ -n $new_command ]]; then
      # Save the original shai command to history
      print -s "$original_buffer"

      # SUCCESS: Replace the buffer with the new command
      BUFFER=$new_command
      CURSOR=\${#new_command}

      # Just redisplay the prompt. DO NOT execute.
      zle redisplay
    else
      # FAILURE: The shai command failed (e.g., API error).
      # Restore original buffer and execute it so user sees the error
      BUFFER="$original_buffer"
      zle accept-line
    fi
  else
    # The line *doesn't* start with "shai".
    # This means it's either a normal command, OR it's the *result*
    # of our transformation (e.g., "docker ps").
    #
    # So, call the ORIGINAL 'Enter' action to run it.
    zle accept-line
  fi
}

# Create the new widget
zle -N shai_enter_to_expand

# Bind the 'Enter' key (^M) to our new widget
# This hijacks the default 'Enter' behavior.
bindkey '^M' shai_enter_to_expand
`;
