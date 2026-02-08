import { createEnv } from "@t3-oss/env-core";
import { z } from "zod";

const env = createEnv({
  server: {
    GEMINI_MODEL: z.string().default("gemini-2.5-flash-lite"),
    GOOGLE_GENERATIVE_AI_API_KEY: z
      .string()
      .min(1, "GEMINI_API_KEY is required for Gemini API access"),
    SHAI_HISTORY_DISABLE: z.string().default("false"),
    SHAI_HISTORY_LINES: z.int().default(50),
  },

  runtimeEnvStrict: {
    GEMINI_MODEL: Deno.env.get("GEMINI_MODEL"),
    GOOGLE_GENERATIVE_AI_API_KEY: Deno.env.get("GOOGLE_GENERATIVE_AI_API_KEY"),
    SHAI_HISTORY_DISABLE: Deno.env.get("SHAI_HISTORY_DISABLE"),
    SHAI_HISTORY_LINES: Deno.env.get("SHAI_HISTORY_LINES"),
  },

  isServer: typeof window === "undefined",
  emptyStringAsUndefined: true,
});

export default env;
