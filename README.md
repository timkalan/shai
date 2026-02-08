# shai

Want to get something done in the shell but can't quite remember how? Too shy to
ask your coworkers? Too deep in the AI sauce to Google it? `shai` has your back.

## Installation

Run the following command in your terminal. This will download the correct
`shai` binary for your system, make it executable, and move it to
`/usr/local/bin`.

```sh
curl -fsSL https://github.com/timkalan/shai/raw/main/scripts/install.sh | sh
```

To enable shell integration (for now, `zsh` only), add this at the end of your
`.zshrc`. Note that currently, you need to have `GOOGLE_GENERATIVE_AI_API_KEY`
in your environment.

```sh
# or just use a .env file
export GOOGLE_GENERATIVE_AI_API_KEY=<your-api-key>

# Enable immediate history writing (recommended for best results)
setopt INC_APPEND_HISTORY

eval "$(shai --zsh-init)"
```

and then restart your shell (or `source ~/.zshrc`).

## Usage

Just call `shai` with your prompt and let the magic happen. shai uses the
`gemini-2.5-flash-lite` model so you can use a free api key.

### History Awareness

shai can read your shell history to provide better context for command
generation. It automatically reads recent commands from your `.zsh_history` file
and includes them in the AI prompt (excluding common noise like `cd`, `ls`,
`pwd`).

**Note:** For the best experience with history awareness, ensure you have
`setopt INC_APPEND_HISTORY` in your `.zshrc` (shown in installation section
above). This ensures commands are written to history immediately, making recent
commands available to shai.

**Disable history:**

```bash
# Per-command
shai --no-history <prompt>

# Globally via environment variable
export SHAI_HISTORY_DISABLE=true
```

**Configure history lines:**

```bash
# Default is 50 lines, maximum 10 commands sent to AI
export SHAI_HISTORY_LINES=100
```

**Debug mode** (see what history is being used):

```bash
shai --debug <prompt>
```

## Development

### Testing Widget Changes

Since shai's magic is in the Zsh widget (the Enter key interception), you need
to reload it when making changes to `src/zsh-init.ts`:

```bash
# Quick install and reload for development
deno task install && eval "$(shai --zsh-init)"

# Now test it:
shai list files in current directory
```

**Available tasks:**

- `deno task shai <prompt>` - Run locally without compiling
- `deno task install` - Compile and install to /usr/local/bin
- `deno task compile` - Just compile the binary
- `deno task all` - Format, lint, and type-check (run before pushing)

## Roadmap

- [x] **History**: Give shai access to more context
- [ ] **Models**: We should allow our users to pick their models/providers
- [ ] **Bash Support**: Add init script and support for Bash shell.
- [ ] **Explain Mode**: Add a flag to explain the generated command before
      running it.
- [ ] **Self Update**: Add a command to upgrade to the latest version
      automatically.
