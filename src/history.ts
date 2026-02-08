/**
 * Reads the zsh history file and returns filtered useful commands.
 * Handles extended history format with timestamps.
 */

// Commands to filter out as noise
const NOISE_COMMANDS = new Set([
  "cd",
  "ls",
  "pwd",
  "clear",
  "exit",
  "shai", // Avoid recursion
]);

const ZSH_HISTORY_PATH = `${Deno.env.get("HOME") ?? "/tmp"}/.zsh_history`;

/**
 * Get filtered history context for AI prompt.
 * Reads last N lines from history, filters noise, returns meaningful commands.
 */
export async function getHistoryContext(
  rawLines: number = 50,
  maxResults: number = 10,
): Promise<string[]> {
  const rawHistory = await readHistory(rawLines);
  return filterHistory(rawHistory, maxResults);
}

/**
 * Read the last N commands from zsh history file
 */
async function readHistory(maxLines: number): Promise<string[]> {
  try {
    const historyPath = Deno.env.get("HISTFILE") || ZSH_HISTORY_PATH;

    // Check if file exists and is readable
    try {
      await Deno.stat(historyPath);
    } catch {
      return [];
    }

    // Read the file
    const content = await Deno.readTextFile(historyPath);
    const lines = content.split("\n").filter((line) => line.trim() !== "");

    // Get last N lines
    const recentLines = lines.slice(-maxLines);

    // Parse each line (handle extended history format)
    const commands: string[] = [];
    for (const line of recentLines) {
      const command = parseZshHistoryLine(line);
      if (command) {
        commands.push(command);
      }
    }

    return commands;
  } catch {
    return [];
  }
}

/**
 * Parse a zsh history line.
 * Handles extended format: `: timestamp:0;command`
 * and simple format: `command`
 */
function parseZshHistoryLine(line: string): string | null {
  // Extended history format: `: timestamp:0;command`
  if (line.startsWith(":")) {
    const semicolonIndex = line.indexOf(";");
    if (semicolonIndex !== -1) {
      return line.substring(semicolonIndex + 1);
    }
  }

  // Simple format: just the command
  return line;
}

/**
 * Filter history to remove noise and duplicates.
 * Returns the last N meaningful commands, deduplicated across entire history.
 */
function filterHistory(
  commands: string[],
  maxResults: number,
): string[] {
  const filtered: string[] = [];
  const seen = new Set<string>();

  // Iterate in reverse to keep most recent occurrence
  for (let i = commands.length - 1; i >= 0; i--) {
    const trimmed = commands[i].trim();

    // Skip empty commands
    if (trimmed.length === 0) continue;

    // Skip commands that are too short
    if (trimmed.length < 3) continue;

    // Skip noise commands (check first word)
    const firstWord = trimmed.split(/\s+/)[0];
    if (NOISE_COMMANDS.has(firstWord)) continue;

    // Skip duplicates (keep only most recent)
    if (seen.has(trimmed)) continue;
    seen.add(trimmed);

    filtered.unshift(trimmed); // Add to front to maintain order
  }

  // Return last N filtered commands
  return filtered.slice(-maxResults);
}
