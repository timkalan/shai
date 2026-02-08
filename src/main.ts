import { generateObject } from "ai";
import { google } from "@ai-sdk/google";
import env from "./env.ts";
import z from "zod";
import { ZSH_INIT_SCRIPT } from "./zsh-init.ts";
import { getHistoryContext } from "./history.ts";
import { parseArgs } from "@std/cli/parse-args";

const CommandSchema = z.object({
  command: z
    .string()
    .describe("A safe system command to execute based on user input"),
});

const generateCommand = async (
  userPrompt: string,
  historyContext: string[],
) => {
  const os = Deno.build.os === "darwin" ? "macOS" : Deno.build.os;
  const shellPath = Deno.env.get("SHELL");
  const shell = shellPath ? shellPath.split("/").pop() : "zsh";

  // Build system prompt with history context
  let systemPrompt = `
You are a command-line assistant running on ${os} using ${shell}. Generate a single,
valid system command string based on the user's request. Ensure the command is syntactically
correct for ${shell} on ${os}. Only include safe, non-destructive commands.
`;

  if (historyContext.length > 0) {
    systemPrompt += `\n\nRecent shell commands:\n${
      historyContext
        .map((cmd) => `- ${cmd}`)
        .join("\n")
    }\n`;
  }

  const { object } = await generateObject({
    model: google(env.GEMINI_MODEL),
    schema: CommandSchema,
    system: systemPrompt,
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

// Parse command-line arguments
const parsed = parseArgs(Deno.args, {
  boolean: ["zsh-init", "no-history", "debug"],
  "--": true, // Stop parsing at '--'
});

// Handle --zsh-init flag
if (parsed["zsh-init"]) {
  console.log(ZSH_INIT_SCRIPT);
  Deno.exit(0);
}

// Determine if history should be used
const useHistory = !parsed["no-history"] &&
  env.SHAI_HISTORY_DISABLE !== "true";

const userPrompt = parsed._.join(" ");

if (!userPrompt) {
  console.error("shai: Please provide a prompt.");
  Deno.exit(1);
}

try {
  // Load history if enabled
  let historyContext: string[] = [];
  if (useHistory) {
    historyContext = await getHistoryContext(env.SHAI_HISTORY_LINES, 10);
  }

  // Debug output
  if (parsed.debug) {
    console.error(
      `History: ${
        historyContext.length > 0
          ? `loaded ${historyContext.length} commands`
          : "unavailable"
      }`,
    );
  }

  const result = await generateCommand(userPrompt, historyContext);
  console.log(result.command);
} catch (err) {
  const errMessage = err instanceof Error ? err.message : String(err);
  console.error("shai: Failed to generate command:", errMessage);
  Deno.exit(1);
}
