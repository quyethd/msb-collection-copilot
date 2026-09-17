export type ConversationContext = {
  active_cif: string;
  previous_intent?: string;
  previous_topic?: string;
  previous_user_question?: string;
  previous_path?: string;
  last_simulation_field?: string;
  last_simulation_changes?: Record<string, string | number>;
};

export type ChatMessage = {
  id: string;
  role: 'user' | 'assistant' | 'system-status';
  createdAt: string;
  content: string;
  intent?: string;
  topic?: string;
  pending_clarification?: string;
  path?: string;
  sections?: any[];
  sources?: any[];
  status?: 'pending' | 'complete' | 'error';
};

const VERSION = 'v2';
const PREFIX = `msb-copilot-conversation-${VERSION}:`;
export const customerThreadKey = (cif: string) => `${PREFIX}customer:${cif}`;
export const knowledgeThreadKey = () => `${PREFIX}knowledge`;
const keyFor = (cif: string) => customerThreadKey(cif);
const legacyKeyFor = (cif: string) => `${PREFIX}${cif}`;

function readKey(key: string): ChatMessage[] {
  try {
    const parsed = JSON.parse(sessionStorage.getItem(key) || '[]');
    return Array.isArray(parsed) ? parsed.filter(x => x && (x.role === 'user' || x.role === 'assistant') && typeof x.content === 'string') : [];
  } catch { return []; }
}

function writeKey(key: string, messages: ChatMessage[]) {
  try {
    sessionStorage.setItem(key, JSON.stringify(messages.slice(-60).map(({id, role, createdAt, content, intent, topic, pending_clarification, path, sections, sources, status}) => ({id, role, createdAt, content, intent, topic, pending_clarification, path, sections, sources, status}))));
  } catch { /* sessionStorage can be unavailable in privacy mode */ }
}

export function loadConversation(cif: string): ChatMessage[] {
  const current = readKey(keyFor(cif));
  return current.length ? current : readKey(legacyKeyFor(cif));
}

export function saveConversation(cif: string, messages: ChatMessage[]) {
  writeKey(keyFor(cif), messages);
}

export function clearConversation(cif: string) {
  try { sessionStorage.removeItem(keyFor(cif)); } catch { /* no-op */ }
}

export function loadKnowledgeConversation(): ChatMessage[] {
  return readKey(knowledgeThreadKey());
}

export function saveKnowledgeConversation(messages: ChatMessage[]) {
  writeKey(knowledgeThreadKey(), messages);
}

export function clearAllConversations() {
  try {
    const keys: string[] = [];
    for (let index = 0; index < sessionStorage.length; index += 1) {
      const key = sessionStorage.key(index);
      if (key?.startsWith(PREFIX)) keys.push(key);
    }
    keys.forEach(key => sessionStorage.removeItem(key));
  } catch { /* no-op */ }
}

export function saveConversationKey(key: string, messages: ChatMessage[]) {
  if (key.startsWith(PREFIX) && !messages.some(message => message.status === 'pending')) writeKey(key, messages);
}

export function clearConversationKey(key: string) {
  try {
    if (key.startsWith(PREFIX)) sessionStorage.removeItem(key);
  } catch { /* no-op */ }
}

export function loadConversationKey(key: string): ChatMessage[] {
  if (!key.startsWith(PREFIX)) return [];
  const current = readKey(key);
  if (current.length || !key.startsWith(`${PREFIX}customer:`)) return current;
  const cif = key.slice(`${PREFIX}customer:`.length);
  return readKey(legacyKeyFor(cif));
}

export function visibleAnswerText(message: ChatMessage): string {
  if (message.sections?.length) {
    return message.sections.map(section => {
      const title = typeof section?.title === 'string' ? section.title : '';
      const body = Array.isArray(section?.items)
        ? section.items.join('\n')
        : typeof section?.content === 'string' ? section.content : '';
      return [title, body].filter(Boolean).join('\n');
    }).filter(Boolean).join('\n\n');
  }
  return message.content;
}

export function responseStatus(response: {metadata?: {path?: string}; question_intent?: string; tools_used?: string[]}): string {
  if (response.metadata?.path === 'RAG_QWEN') return 'Đã tra cứu kho kiến thức';
  if (response.question_intent === 'SIMULATION') return 'Đã chạy mô phỏng theo Decision Core';
  if (response.question_intent === 'DECISION_EXPLANATION') return 'Đã đối chiếu Decision Core';
  if (response.tools_used?.length) return 'Đã lấy dữ liệu khách hàng';
  return 'Đã hoàn tất câu trả lời';
}

export function isNearBottom(element: {scrollHeight: number; scrollTop: number; clientHeight: number} | null, threshold = 140): boolean {
  if (!element) return true;
  return element.scrollHeight - element.scrollTop - element.clientHeight < threshold;
}

export function buildConversationContext(cif: string, messages: ChatMessage[]): ConversationContext {
  const prior = [...messages].reverse().find(message => message.role === 'assistant' && message.status === 'complete');
  const priorUser = [...messages].reverse().find(message => message.role === 'user');
  const ctx: ConversationContext = {active_cif: cif, previous_intent: prior?.intent, previous_topic: prior?.topic ?? prior?.intent, previous_user_question: priorUser?.content, previous_path: prior?.path};
  if (prior?.pending_clarification) (ctx as any).pending_clarification = prior.pending_clarification;
  return ctx;
}

export function followUpSuggestions(message?: ChatMessage): string[] {
  if (!message || message.role !== 'assistant') return [];
  if (message.path === 'RAG_QWEN') return ['Decision Core là gì?', 'Khả năng tự thanh toán là gì?', 'GreenNode AI đóng vai trò gì?'];
  if (message.intent === 'SIMULATION') return ['Vậy lúc đó nên làm gì?', 'Nếu dòng tiền 30 ngày cũng giảm thì sao?', 'Điểm quyết định có thay đổi không?'];
  if (message.intent === 'CASHFLOW') return ['Thế còn 30 ngày?', 'Nếu tiền vào 7 ngày bằng 0 thì sao?', 'Có cam kết thanh toán nào đang mở không?'];
  return ['Dòng tiền gần đây?', 'Nếu dòng tiền bằng 0?', 'Điểm 47 được tính thế nào?'];
}

export const INITIAL_SUGGESTIONS = [
  'Tại sao hôm nay chưa nên gọi khách hàng này?',
  'Dòng tiền gần đây của khách hàng thế nào?',
  'Khách hàng có cam kết thanh toán nào đang mở không?',
  'Nếu dòng tiền 7 ngày bằng 0 thì quyết định có thay đổi không?',
];
