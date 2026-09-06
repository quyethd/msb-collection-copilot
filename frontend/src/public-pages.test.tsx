// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { LoginPage, PublicLanding } from './public-pages';

describe('TASK-011I public shell', () => {
  it('renders a full-width landing without the operational sidebar', () => {
    const html = renderToStaticMarkup(<PublicLanding />);
    expect(html).toContain('Không tìm khách hàng nợ nhiều nhất.');
    expect(html).toContain('Powered by GreenNode AI');
    expect(html).toContain('Đăng nhập hệ thống');
    expect(html).toContain('Nền Tảng AI GreenNode');
    expect(html).not.toContain('Điều hướng chính');
  });

  it('renders login fields without demo credentials in public markup', () => {
    const html = renderToStaticMarkup(<LoginPage />);
    expect(html).toContain('Tên đăng nhập');
    expect(html).toContain('Mật khẩu');
    expect(html).toContain('Đăng nhập');
    expect(html).not.toContain('admin');
  });
});
