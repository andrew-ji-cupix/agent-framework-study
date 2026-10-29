'use agent';
import { createProvider } from '@earendil-works/pi-ai';
import { anthropicMessagesApi } from '@earendil-works/pi-ai/api/anthropic-messages.lazy';
import { openrouterProvider } from '@earendil-works/pi-ai/providers/openrouter';
import { setProvider, useModel } from '@flue/runtime';
import { INSTRUCTIONS, MODEL } from '/shared/ladder.ts';

// 프록시 경유: 내장 openrouter 카탈로그를 프록시 주소로 다시 등록한다 (flue run은 app.ts를 읽지 않는다)
setProvider(
  createProvider({
    id: 'openrouter',
    auth: { apiKey: { name: 'proxy', resolve: async () => ({ auth: { apiKey: process.env.LLM_API_KEY } }) } },
    models: openrouterProvider()
      .getModels()
      .filter((model) => model.api === 'anthropic-messages')
      .map((model) => ({ ...model, baseUrl: process.env.LLM_ANTHROPIC_BASE_URL! })),
    api: anthropicMessagesApi(),
  }),
);

export function IssueAssistant() {
  useModel(`openrouter/${MODEL}`);
  return INSTRUCTIONS;
}
