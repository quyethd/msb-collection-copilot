// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { renderToStaticMarkup } from 'react-dom/server';
import { LoginPage, PublicLanding } from './public-pages';

describe('TASK-016 landing pitch story', () => {
  it('renders a full-width landing without the operational sidebar', () => {
    const html = renderToStaticMarkup(<PublicLanding />);
    expect(html).toContain('Không tìm khách hàng nợ nhiều nhất.');
    expect(html).toContain('Powered by GreenNode AI');
    expect(html).toContain('Trải nghiệm bản demo');
    for (const text of ['01 · BÀI TOÁN','02 · GIẢI PHÁP','03 · HÀNH TRÌNH NGƯỜI DÙNG','TÓM TẮT AI CHO HỒ SƠ','SYN002846','47 / 100','MÔ PHỎNG WHAT-IF','WEB + ZALO','CÁCH AI HOẠT ĐỘNG','GREENNODE TRONG SẢN PHẨM','TÁC ĐỘNG + BẰNG CHỨNG','LỘ TRÌNH + FAQ','Debt Radar']) expect(html).toContain(text);
    for (const asset of ['zalo-demo-live-context.png','greennode-in-product.png','user-journey.png','system-architecture.png']) expect(html).toContain(asset);
    expect(html).not.toContain('Điều hướng chính');
  });

  it('preserves the business explanation and public language boundary', () => {
    const html = renderToStaticMarkup(<PublicLanding />);
    for (const text of ['Điểm cơ hội thu hồi là điểm ưu tiên tương đối','không có nghĩa hôm nay nhất thiết phải gọi','Mô phỏng không thay đổi dữ liệu thật','Decision Core tính lại kết quả','AgentBase giúp Trợ lý xác định đúng dữ liệu và công cụ','GLM 5.2','Vector Database + Qwen Flash']) expect(html).toContain(text);
    for (const forbidden of ['TASK-013','TASK-014','TASK-015','TASK-016','Codex','commit','merge','deploy','audit','regression','get_current_decision','MAX_TOOL_CALLS','fallback level','msb_policy','msb_recovery','msb_nba']) expect(html).not.toContain(forbidden);
  });

  it('ships the mandatory landing assets', () => {
    for (const asset of ['zalo-demo-live-context.png','greennode-in-product.png']) expect(existsSync(resolve(__dirname, '../public/landing-story', asset))).toBe(true);
  });

  it('renders login fields without demo credentials in public markup', () => {
    const html = renderToStaticMarkup(<LoginPage />);
    expect(html).toContain('Tên đăng nhập');
    expect(html).toContain('Mật khẩu');
    expect(html).toContain('Đăng nhập');
    expect(html).not.toContain('admin');
  });
});
