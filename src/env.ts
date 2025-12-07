import { createEnv } from "@t3-oss/env-core";
import { z } from "zod";

const env = createEnv({
  server: {
    GEMINI_MODEL: z.string().default("gemini-2.5-flash-lite"),
    GOOGLE_GENERATIVE_AI_API_KEY: z.string().min(
      1,
      "GEMINI_API_KEY is required for Gemini API access",
    ),
  },

  runtimeEnvStrict: {
    GEMINI_MODEL: Deno.env.get("GEMINI_MODEL"),
    GOOGLE_GENERATIVE_AI_API_KEY: Deno.env.get("GOOGLE_GENERATIVE_AI_API_KEY"),
  },

  isServer: typeof window === "undefined",
  emptyStringAsUndefined: true,
});

export default env;
