import { generateObject } from "ai";
import { google } from "@ai-sdk/google";
import env from "./env.ts";
import z from "zod";

const ZSH_INIT_SCRIPT = `
# This widget re-defines what 'Enter' (accept-line) does.
shai_enter_to_expand() {
  
  # Check if the current line buffer starts with "shai "
  if [[ $BUFFER == shai\\ * ]]; then
    
    # It's a shai command. We want to *transform* it, not execute it yet.
    local prompt=\${BUFFER#shai }
    
    # Define a spinner function for animation
    _shai_spinner() {
      # Hide cursor
      printf "\\e[?25l" > /dev/tty
      local spinner="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
      while true; do
        for i in {1..10}; do
          # Print to /dev/tty to show to user, cursor return \\r to overwrite, \\e[K to clear line
          printf "\\r\\e[K\\e[36m%s\\e[0m Generating..." "\${spinner[\$i]}" > /dev/tty
          sleep 0.1
        done
      done
    }

    # Start the spinner in the background
    # Use &| to background and disown immediately, suppressing job control messages
    _shai_spinner &|
    local spinner_pid=$!

    # Run the shai tool and capture the command (stdout)
    # Errors (stderr) will go to /dev/tty to be seen
    local new_command
    new_command=$(command shai "$prompt" 2>/dev/tty)
    
    # Kill the spinner
    kill "$spinner_pid" 2>/dev/null
    
    # Clear the spinner line and restore cursor
    printf "\\r\\e[K\\e[?25h" > /dev/tty
    
    # Check if we got a command back
    if [[ -n $new_command ]]; then
      # Save the original shai command to history
      print -s "$BUFFER"

      # SUCCESS: Replace the buffer with the new command
      BUFFER=$new_command
      CURSOR=\${#new_command}
      
      # Just redisplay the prompt. DO NOT execute.
      zle redisplay
    else
      # FAILURE: The shai command failed (e.g., API error).
      # In this case, just run the original "shai ..." command
      # so the user can see the error output from stderr.
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

// Check if the user is asking for the init script
if (Deno.args[0] === "--zsh-init") {
  console.log(ZSH_INIT_SCRIPT);
  Deno.exit(0);
}

const CommandSchema = z.object({
  command: z
    .string()
    .describe("A safe system command to execute based on user input"),
});

const generateCommand = async (userPrompt: string) => {
  const os = Deno.build.os === "darwin" ? "macOS" : Deno.build.os;
  const shellPath = Deno.env.get("SHELL");
  const shell = shellPath ? shellPath.split("/").pop() : "zsh";

  const { object } = await generateObject({
    model: google(env.GEMINI_MODEL),
    schema: CommandSchema,
    system:
      `You are a command-line assistant running on ${os} using ${shell}. Generate a single, valid system command string based on the user's request. Ensure the command is syntactically correct for ${shell} on ${os}. Only include safe, non-destructive commands.`,
    messages: [
      {
        role: "user",
        content: [
          {
            type: "text",
            text: userPrompt,
          },
        ],
      },
    ],
  });

  return object;
};

const userPrompt = Deno.args.join(" ");

if (!userPrompt) {
  console.error("shai: Please provide a prompt.");
  Deno.exit(1);
}

try {
  const result = await generateCommand(userPrompt);
  console.log(result.command);
} catch (err) {
  const errMessage = err instanceof Error ? err.message : String(err);
  console.error("shai: Failed to generate command:", errMessage);
  Deno.exit(1);
}
