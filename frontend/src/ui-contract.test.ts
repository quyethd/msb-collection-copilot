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
    for(const label of ['Hôm nay cần xử lý ai?','HÀNH ĐỘNG ĐỀ XUẤT HÔM NAY','Vì sao hệ thống đề xuất như vậy?','Lịch sử thay đổi quyết định','Hỏi Copilot về khách hàng này']) expect(source).toContain(label);
    expect(source).toContain('SYN002846');
    expect(source).toContain('Không thể tải dữ liệu. Vui lòng thử lại.');
  });
  it('does not bundle credential names or bearer credentials',()=>{
    expect(source).not.toMatch(/API_KEY|CLIENT_SECRET|Authorization|Bearer/);
  });
});
