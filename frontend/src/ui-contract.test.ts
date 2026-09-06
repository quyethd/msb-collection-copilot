import {describe,expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

const source=readFileSync(resolve(__dirname,'main.tsx'),'utf8');
describe('TASK-009 demo UI contract',()=>{
  it('keeps the three accepted event types only',()=>{
    expect(source.match(/CASH_IN_RECEIVED/g)?.length).toBeGreaterThan(0);
    expect(source.match(/PAYMENT_PROMISE_CREATED/g)?.length).toBeGreaterThan(0);
    expect(source.match(/PAYMENT_PROMISE_BROKEN/g)?.length).toBeGreaterThan(0);
    expect(source).not.toContain('AEV');
  });
  it('renders customer-facing Vietnamese labels and accepted hero facts',()=>{
    for(const label of ['HÀNH ĐỘNG ĐỀ XUẤT HÔM NAY','Vì sao hệ thống đề xuất như vậy?','Lịch sử thay đổi quyết định','Hỏi Trợ lý Thu hồi']) expect(source).toContain(label);
    expect(source).toContain('SYN002846');
    expect(source).toContain('Không thể tải dữ liệu. Vui lòng thử lại.');
  });
  it('does not bundle credential names or bearer credentials',()=>{
    expect(source).not.toMatch(/API_KEY|CLIENT_SECRET|Authorization|Bearer/);
  });
  it('exposes the supported scenario explorer without raw decision codes',()=>{
    for(const label of ['Tạo tình huống thử','Xem quyết định thay đổi thế nào','Đặt lại','Tình huống thử không làm thay đổi dữ liệu khách hàng.','TRƯỚC TÌNH HUỐNG','SAU TÌNH HUỐNG']) expect(source).toContain(label);
    for(const field of ['inflow_7d','net_cashflow_30d','ptp_state','promise_date','latest_business_outcome']) expect(source).toContain(field);
    expect(source).toContain("api('/demo/simulate'");
    expect(source).not.toContain('NBA-300');
  });
  it('normalizes accepted tool envelopes and keeps the local proxy on 18080',()=>{
    expect(source).toContain('const toolData=(response:any)=>response?.data??response;');
    expect(source).toContain('setCustomer(toolData(ctx));');
    expect(source).toContain('setDecision(toolData(nba));');
    expect(readFileSync(resolve(__dirname,'../vite.config.ts'),'utf8')).toContain("const target='http://127.0.0.1:18080'");
  });
  it('marks only the actual page item active',()=>{
    const pages=readFileSync(resolve(__dirname,'pages.tsx'),'utf8');
    expect(pages).toContain("aria-current={page===target?'page':undefined}");
    expect(source).toContain('useState<Page>(pageFromPath)');
    expect(source).toContain("'/app/priority':'priority'");
  });
  it('uses the system overview as the public landing and keeps the app shell operational',()=>{
    expect(source).toContain("import {SystemOverviewPage} from './pages/system-overview/SystemOverviewPage';");
    expect(source).toContain('return <PublicLanding/>');
    expect(readFileSync(resolve(__dirname,'public-pages.tsx'),'utf8')).toContain('<SystemOverviewPage');
    expect(readFileSync(resolve(__dirname,'pages.tsx'),'utf8')).not.toContain('secondary-navitem');
  });
  it('uses browser-safe demo routes for protected data',()=>{
    for(const route of ["api('/demo/customer-360'","api('/demo/next-best-action'","api('/demo/simulate'"]) expect(source).toContain(route);
    for(const route of ["api('/tools/get_customer_360'","api('/tools/get_next_best_action'","api('/tools/simulate_decision'"]) expect(source).not.toContain(route);
  });
  it('uses one shared question catalog for landing and drawer',()=>{
    expect(source).toContain("import {assistantQuestionCatalog,commonAssistantQuestions} from './assistant-question-catalog';");
    expect(source).toContain('Xem thêm 6 câu hỏi');
    expect(readFileSync(resolve(__dirname,'assistant-question-catalog.ts'),'utf8').match(/question: '/g)).toHaveLength(10);
    expect(readFileSync(resolve(__dirname,'pages/system-overview/content.ts'),'utf8')).toContain("from '../../assistant-question-catalog'");
  });
  it('renders the assistant above page overlays through a portal',()=>{
    expect(source).toContain('createPortal(content,document.body)');
    expect(readFileSync(resolve(__dirname,'navigation.css'),'utf8')).toContain('.drawer-backdrop{z-index:1000;');
  });
});
