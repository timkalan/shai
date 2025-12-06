# shai

Want to get something done in the shell but can't quite remember how? Too shy to
ask your coworkers? Too deep in the AI sauce to Google it? `shai` has your back.

## Installation

Run the following command in your terminal. This will download the correct
`shai` binary for your system, make it executable, and move it to
`/usr/local/bin`.

```sh
curl -fsSL https://github.com/timkalan/shai/raw/main/install.sh | sh
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

## Roadmap

- [ ] **Bash Support**: Add init script and support for Bash shell.
- [ ] **Explain Mode**: Add a flag to explain the generated command before
      running it.
- [ ] **Self Update**: Add a command to upgrade to the latest version
      automatically.
