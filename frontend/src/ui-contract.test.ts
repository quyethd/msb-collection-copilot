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
    const routing=readFileSync(resolve(__dirname,'app-routing.ts'),'utf8');
    expect(source).toContain("import {pageFromPath,pathForPage} from './app-routing';");
    expect(routing).toContain("'/app/priority'");
    expect(routing).toContain("'/app/zalo'");
  });
  it('keeps the public landing separate and the app shell operational',()=>{
    expect(source).toContain('return <PublicLanding/>');
    expect(readFileSync(resolve(__dirname,'public-pages.tsx'),'utf8')).toContain('story-hero');
    expect(readFileSync(resolve(__dirname,'pages.tsx'),'utf8')).not.toContain('secondary-navitem');
  });
  it('uses browser-safe demo routes for protected data',()=>{
    for(const route of ["api('/demo/customer-360'","api('/demo/next-best-action'","api('/demo/simulate'"]) expect(source).toContain(route);
    for(const route of ["api('/tools/get_customer_360'","api('/tools/get_next_best_action'","api('/tools/simulate_decision'"]) expect(source).not.toContain(route);
  });
  it('uses one shared question catalog for landing and drawer',()=>{
    expect(source).toContain("import {assistantQuestionCatalog,commonAssistantQuestions} from './assistant-question-catalog';");
    expect(source).toContain('Xem thêm 10 câu hỏi');
    expect(readFileSync(resolve(__dirname,'assistant-question-catalog.ts'),'utf8').match(/question: '/g)).toHaveLength(14);
    expect(readFileSync(resolve(__dirname,'pages/system-overview/content.ts'),'utf8')).toContain("from '../../assistant-question-catalog'");
  });
  it('keeps the first four suggested questions on the shared catalog',()=>{
    const catalog=readFileSync(resolve(__dirname,'assistant-question-catalog.ts'),'utf8');
    for(const q of ['Tại sao hôm nay chưa nên gọi khách hàng này?','Dòng tiền gần đây của khách hàng thế nào?','Khách hàng có cam kết thanh toán nào đang mở không?','Nếu dòng tiền 7 ngày bằng 0 thì quyết định có thay đổi không?']) expect(catalog).toContain(q);
  });
  it('adds project-knowledge suggestions under a dedicated group',()=>{
    const catalog=readFileSync(resolve(__dirname,'assistant-question-catalog.ts'),'utf8');
    expect(catalog).toMatch(/Kiến thức sản phẩm/);
    for(const q of ['CALL và CBS khác nhau thế nào?','GreenNode AI đóng vai trò gì trong hệ thống?','Điểm Cơ hội thu hồi được tính như thế nào?','Trợ lý có tự quyết định phương án xử lý không?']) expect(catalog).toContain(q);
    expect(catalog).toContain("assistantQuestionCatalog.slice(0, 4)");
  });
  it('renders generic pending state and route-confirmed RAG sources',()=>{
    expect(source).toContain("setStatus('Đang xử lý câu hỏi...')");
    expect(source).not.toContain("Đang tìm trong kho kiến thức...");
    expect(source).not.toContain("GreenNode AI đang tổng hợp câu trả lời...");
    expect(source).toContain("r.metadata?.path==='RAG_QWEN'");
    expect(source).toContain('setStatus(responseStatus(r))');
    expect(source).toContain('sources:r.sources||[]');
    expect(source).not.toContain("setStatus('Đã lấy quyết định nghiệp vụ')");
  });
  it('renders the assistant above page overlays through a portal',()=>{
    expect(source).toContain('createPortal(content,document.body)');
    expect(readFileSync(resolve(__dirname,'navigation.css'),'utf8')).toContain('.drawer-backdrop{z-index:1000;');
  });
});
