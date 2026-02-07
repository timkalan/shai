export const ZSH_INIT_SCRIPT = `
# This widget re-defines what 'Enter' (accept-line) does.
shai_enter_to_expand() {
  # Early return: not a shai command - just execute normally
  [[ $BUFFER != shai\\ * ]] && { zle accept-line; return }

  # Extract the prompt and save original buffer
  local prompt="\${BUFFER#shai }"
  local original_buffer="$BUFFER"

  # Create temp file for command output
  local tmpfile=$(mktemp)
  local shai_pid
  local canceled=0

  # Hide cursor during animation
  printf "\\e[?25l" > /dev/tty

  # Run shai in background (disowned, independent of shell job control)
  (command shai "$prompt" > "$tmpfile" 2>/dev/tty) &|
  shai_pid=$!

  # Unified cleanup handler for all exit scenarios
  # This runs on: normal completion, Ctrl+C, or unexpected termination
  local -a cleanup_cmds=(
    'canceled=1'
    'kill $shai_pid 2>/dev/null'
    'wait $shai_pid 2>/dev/null'
    'printf "\\e[?25h" > /dev/tty'
    '[[ -f "$tmpfile" ]] && rm -f "$tmpfile"'
  )
  trap "\${(j.;.)cleanup_cmds}" EXIT INT TERM

  # Show wave spinner while shai is running
  local spin_idx=1
  local -a wave_frames=("▂▄▆█" "▃▅▇▓" "▄▆█▒" "▅▇▓░" "▆█▒░" "▇▓░▁" "█▒░▂" "▓░▁▃")

  while kill -0 $shai_pid 2>/dev/null && [[ $canceled -eq 0 ]]; do
    BUFFER="\${wave_frames[$spin_idx]}"
    zle redisplay
    spin_idx=$((spin_idx % 8 + 1))
    sleep 0.15
  done

  # Handle cancellation (Ctrl+C pressed)
  if [[ $canceled -eq 1 ]]; then
    BUFFER="$original_buffer"
    CURSOR=\${#original_buffer}
    zle redisplay
    return
  fi

  # Read generated command from temp file
  local new_command=""
  [[ -f "$tmpfile" ]] && new_command=$(cat "$tmpfile")

  # Handle result
  if [[ -n $new_command ]]; then
    # Success: save original to history, show generated command
    print -s "$original_buffer"
    BUFFER=$new_command
    CURSOR=\${#new_command}
    zle redisplay
  else
    # Failure: restore original and execute to show error
    BUFFER="$original_buffer"
    zle accept-line
  fi
}

# Create the new widget
zle -N shai_enter_to_expand

# Bind the 'Enter' key (^M) to our new widget
bindkey '^M' shai_enter_to_expand
`;
