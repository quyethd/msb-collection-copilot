// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { renderToStaticMarkup } from 'react-dom/server';
import { LoginPage, PublicLanding } from './public-pages';

describe('TASK-014 landing story', () => {
  it('renders a full-width landing without the operational sidebar', () => {
    const html = renderToStaticMarkup(<PublicLanding />);
    expect(html).toContain('Không tìm khách hàng nợ nhiều nhất.');
    expect(html).toContain('Powered by GreenNode AI');
    expect(html).toContain('Trải nghiệm bản demo');
    for (const text of ['BÀI TOÁN','GIẢI PHÁP','WEB + ZALO','HÀNH TRÌNH NGƯỜI DÙNG','TRÌNH DIỄN SẢN PHẨM','SYN002846','47 / 100','MÔ PHỎNG TÌNH HUỐNG','HAI LUỒNG TRỢ LÝ','CÁCH HỆ THỐNG HOẠT ĐỘNG','GREENNODE TRONG SẢN PHẨM','AI CÓ KIỂM SOÁT','TÁC ĐỘNG DỰ KIẾN','TÓM TẮT CHO BAN GIÁM KHẢO','CÂU HỎI THƯỜNG GẶP','LỘ TRÌNH']) expect(html).toContain(text);
    for (const asset of ['zalo-demo-live-context.png','greennode-in-product.png','user-journey.png','system-architecture.png','two-assistant-flows.png']) expect(html).toContain(asset);
    expect(html).not.toContain('Điều hướng chính');
  });

  it('preserves the business explanation and public language boundary', () => {
    const html = renderToStaticMarkup(<PublicLanding />);
    for (const text of ['8 / 20','20 / 25','4 / 20','11 / 15','4 / 15','0 / 5','Điểm cơ hội thu hồi là điểm ưu tiên tương đối','không có nghĩa hôm nay nhất thiết phải gọi','Mô phỏng không thay đổi dữ liệu thật','Ước tính theo giả định của bản demo']) expect(html).toContain(text);
    for (const forbidden of ['TASK-013','TASK-014','Codex','commit','merge','deploy','audit','regression','runtime','sidecar','18081','context leak','msb_policy','msb_recovery','msb_nba']) expect(html).not.toContain(forbidden);
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
