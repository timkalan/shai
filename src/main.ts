import { generateObject } from "ai";
import { google } from "@ai-sdk/google";
import env from "./env.ts";
import z from "zod";
import { ZSH_INIT_SCRIPT } from "./zsh-init.ts";

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
    system: `
You are a command-line assistant running on ${os} using ${shell}. Generate a single,
valid system command string based on the user's request. Ensure the command is syntactically
correct for ${shell} on ${os}. Only include safe, non-destructive commands.
`,
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
