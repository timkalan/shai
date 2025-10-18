import { generateObject } from "ai";
import { google } from "@ai-sdk/google";
import env from "./env.ts";
import z from "zod";

const generateCommand = async (userPrompt: string) => {
  const { object } = await generateObject({
    model: google(env.GEMINI_MODEL),
    schema: z.object({
      command: z.string().describe("The command to be executed."),
    }),
    system: "Generate a system command based on user input.",
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
  console.error("Please provide a prompt as a command line argument.");
  Deno.exit(1);
}

const result = await generateCommand(userPrompt);
console.log("Generated Command:", result.command);

// --- Executes the generated command ---
// Note: See the important security warning below.
try {
  console.log("\n--- Executing Command ---");
  // Using "sh -c" executes the raw command string.
  // This is simple but also the source of the security risk.
  const command = new Deno.Command("sh", {
    args: ["-c", result.command],
  });

  // .output() waits for the command to finish and captures its output
  const { code, stdout, stderr } = await command.output();

  if (code === 0) {
    console.log("Output:");
    console.log(new TextDecoder().decode(stdout));
  } else {
    console.error("Error:");
    console.error(new TextDecoder().decode(stderr));
  }
} catch (err) {
  const errMessage = err instanceof Error ? err.message : String(err);
  console.error("Failed to execute command:", errMessage);
}
