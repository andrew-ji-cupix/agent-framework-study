'use agent';
// Flue로 하네스 과제를 실행한다: flue run h1.ts -m "<프롬프트>" --json
import { createProvider } from '@earendil-works/pi-ai';
import { anthropicMessagesApi } from '@earendil-works/pi-ai/api/anthropic-messages.lazy';
import { openrouterProvider } from '@earendil-works/pi-ai/providers/openrouter';
import { setProvider, useModel, useSandbox } from '@flue/runtime';
import { local } from '@flue/runtime/node';

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

export function BugFixer() {
  useModel(`openrouter/${process.env.LLM_MODEL}`);
  useSandbox(local({ cwd: '/workspace' }));
  return '작업 폴더에서 사용자의 요청을 수행하세요.';
}
