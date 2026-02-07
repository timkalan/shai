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
eval "$(shai --zsh-init)"
```

and then restart your shell (or `source ~/.zshrc`).

## Usage

Just call `shai` with your prompt and let the magic happen. shai uses the
`gemini-2.5-flash-lite` model so you can use a free api key.

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

- [ ] **History**: Give shai access to more context
- [ ] **Models**: We should allow our users to pick their models/providers
- [ ] **Bash Support**: Add init script and support for Bash shell.
- [ ] **Explain Mode**: Add a flag to explain the generated command before
      running it.
- [ ] **Self Update**: Add a command to upgrade to the latest version
      automatically.
