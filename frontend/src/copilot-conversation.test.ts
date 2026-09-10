// @vitest-environment jsdom
import {describe,it,expect,beforeEach} from 'vitest';
import {INITIAL_SUGGESTIONS,buildConversationContext,clearAllConversations,clearConversation,customerThreadKey,followUpSuggestions,isNearBottom,knowledgeThreadKey,loadConversation,loadConversationKey,loadKnowledgeConversation,responseStatus,saveConversation,saveConversationKey,saveKnowledgeConversation,visibleAnswerText} from './copilot-conversation';

describe('copilot conversation v2 state',()=>{
  beforeEach(()=>sessionStorage.clear());
  it('preserves ordered messages and reloads from session storage',()=>{
    const messages:any[]=[{id:'1',role:'user',createdAt:'1',content:'Vì sao?'},{id:'2',role:'assistant',createdAt:'2',content:'Giải thích',status:'complete',intent:'DECISION_EXPLANATION',path:'FALLBACK'}];
    saveConversation('SYN002846',messages); expect(loadConversation('SYN002846').map(x=>x.id)).toEqual(['1','2']);
    expect(loadConversation('SYN000001')).toEqual([]);
  });
  it('builds bounded context from the last completed answer',()=>{
    const context=buildConversationContext('SYN002846',[{id:'1',role:'assistant',createdAt:'1',content:'x',status:'complete',intent:'CASHFLOW',path:'LOCAL'},{id:'2',role:'user',createdAt:'2',content:'Thế còn 30 ngày?'}] as any);
    expect(context).toMatchObject({active_cif:'SYN002846',previous_intent:'CASHFLOW',previous_user_question:'Thế còn 30 ngày?',previous_path:'LOCAL'});
    expect(JSON.stringify(context)).not.toContain('decision');
  });
  it('resets only the selected thread and gives deterministic contextual suggestions',()=>{
    saveConversation('SYN002846',[{id:'1',role:'user',createdAt:'1',content:'x'}] as any); saveConversation('SYN000001',[{id:'2',role:'user',createdAt:'2',content:'y'}] as any); clearConversation('SYN002846');
    expect(loadConversation('SYN002846')).toEqual([]); expect(loadConversation('SYN000001')).toHaveLength(1);
    expect(followUpSuggestions({role:'assistant',path:'RAG_QWEN'} as any)[0]).toBe('Decision Core là gì?');
  });
  it('keeps the accepted initial four suggestions',()=>expect(INITIAL_SUGGESTIONS).toHaveLength(4));
  it('keeps customer thread saves keyed to the thread, not the active CIF',()=>{
    const a=[{id:'a',role:'user',createdAt:'1',content:'A'}] as any;
    const b=[{id:'b',role:'user',createdAt:'2',content:'B'}] as any;
    const keyA=customerThreadKey('SYN002846'),keyB=customerThreadKey('SYN000001');
    saveConversationKey(keyA,a);saveConversationKey(keyB,b);
    // A CIF switch loads B; the old A state is never written to B.
    expect(loadConversationKey(keyB).map(x=>x.id)).toEqual(['b']);
    expect(loadConversationKey(keyA).map(x=>x.id)).toEqual(['a']);
    saveConversationKey(keyB,[...loadConversationKey(keyB),{id:'b2',role:'assistant',createdAt:'3',content:'B answer'}] as any);
    expect(loadConversation('SYN002846').map(x=>x.id)).toEqual(['a']);
    expect(loadConversation('SYN000001').map(x=>x.id)).toEqual(['b','b2']);
    saveConversationKey(keyB,[{id:'pending',role:'assistant',createdAt:'4',content:'pending',status:'pending'}] as any);
    expect(loadConversationKey(keyB).map(x=>x.id)).toEqual(['b','b2']);
  });
  it('migrates the prior v2 customer key without mixing it into another CIF',()=>{
    sessionStorage.setItem('msb-copilot-conversation-v2:SYN002846',JSON.stringify([{id:'legacy',role:'user',createdAt:'1',content:'legacy'}]));
    expect(loadConversationKey(customerThreadKey('SYN002846')).map(x=>x.id)).toEqual(['legacy']);
    expect(loadConversationKey(customerThreadKey('SYN000001')).map(x=>x.id)).toEqual([]);
  });
  it('stores knowledge separately and logout cleanup preserves unrelated state',()=>{
    saveConversation('SYN002846',[{id:'a',role:'user',createdAt:'1',content:'customer'}] as any);
    saveConversation('SYN000001',[{id:'b',role:'user',createdAt:'2',content:'customer B'}] as any);
    saveKnowledgeConversation([{id:'k',role:'assistant',createdAt:'3',content:'knowledge',intent:'KNOWLEDGE',path:'RAG_QWEN'}] as any);
    sessionStorage.setItem('unrelated-app-state','keep');
    expect(loadKnowledgeConversation().map(x=>x.id)).toEqual(['k']);
    expect(loadConversation('SYN002846').map(x=>x.id)).toEqual(['a']);
    clearAllConversations();
    expect(loadConversation('SYN002846')).toEqual([]);expect(loadConversation('SYN000001')).toEqual([]);expect(loadKnowledgeConversation()).toEqual([]);
    expect(sessionStorage.getItem('unrelated-app-state')).toBe('keep');
  });
  it('serializes only visible structured answer content',()=>{
    expect(visibleAnswerText({role:'assistant',id:'1',createdAt:'1',content:'hidden fallback',sections:[{title:'Dòng tiền',items:['7 ngày: 48 triệu']},{title:'Giải thích',content:'Dựa trên dữ liệu đã xác nhận.'}]} as any)).toBe('Dòng tiền\n7 ngày: 48 triệu\n\nGiải thích\nDựa trên dữ liệu đã xác nhận.');
  });
  it('reports truthful status only after route metadata exists',()=>{
    expect(responseStatus({})).toBe('Đã hoàn tất câu trả lời');
    expect(responseStatus({metadata:{path:'RAG_QWEN'}})).toBe('Đã tra cứu kho kiến thức');
    expect(responseStatus({question_intent:'DECISION_EXPLANATION',tools_used:['get_next_best_action']})).toBe('Đã đối chiếu Decision Core');
  });
  it('preserves bottom intent but does not force a reader back down',()=>{
    expect(isNearBottom({scrollHeight:1000,scrollTop:700,clientHeight:300})).toBe(true);
    expect(isNearBottom({scrollHeight:2000,scrollTop:100,clientHeight:300})).toBe(false);
  });
});
