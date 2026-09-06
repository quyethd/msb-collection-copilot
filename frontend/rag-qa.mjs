import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const VIEWPORTS = [
  [1366, 768],
  [1440, 900],
  [1920, 1080],
  [390, 844],
];
const BANNED = [
  'msb-collection-copilot-spike',
  'COLLECTION_TOOL_API_KEY',
  'GREENNODE_CLIENT_SECRET',
  'LLM_API_KEY',
  'CLIENT_SECRET',
  'Authorization: Bearer',
];
const OVERCLAIM = [
  'tăng tỷ lệ thu hồi',
  'tỷ lệ thu hồi',
  'chắc chắn sẽ trả',
];

const browser = await chromium.launch({ headless: true });
let knowledgeAnswered = false;
try {
  for (const [width, height] of VIEWPORTS) {
    const page = await browser.newPage({ viewport: { width, height } });
    await page.goto('http://127.0.0.1:5173/gioi-thieu');
    await page.locator('.so-audience-nav').waitFor();

    const text = await page.evaluate(() => document.body.innerText);
    for (const visible of [
      'Nền Tảng AI GreenNode',
      'GreenNode AgentBase',
      'Qwen Flash',
      'GreenNode Vector Database',
      'Nhúng đa ngôn ngữ cục bộ',
      'TASK-011H-V2',
      'Trợ Lý Hiểu Cả Quyết Định Và Kiến Thức Hệ Thống',
      'Đã kiểm chứng kết nối GreenNode Vector Database và truy xuất kho kiến thức (RAG) trên môi trường demo / live proof.',
      'LUỒNG KIẾN THỨC HỆ THỐNG',
    ]) {
      assert.ok(text.includes(visible), `${width}: landing must mention "${visible}"`);
    }
    for (const banned of BANNED) {
      assert.ok(!text.includes(banned), `${width}: banned string "${banned}" must not appear`);
    }
    for (const forbidden of OVERCLAIM) {
      assert.ok(!text.includes(forbidden), `${width}: overclaim "${forbidden}" must not appear`);
    }
    assert.ok(!/AgentBase[\s\S]{0,40}PASS/i.test(text), `${width}: AgentBase proof must not overclaim`);

    const arch = await page.evaluate(() => {
      const paths = document.querySelectorAll('.so-arch-path');
      return {
        count: paths.length,
        decision: !!document.querySelector('.so-arch-path-decision'),
        knowledge: !!document.querySelector('.so-arch-path-knowledge'),
      };
    });
    assert.equal(arch.count, 2, `${width}: two architecture paths expected`);
    assert.ok(arch.decision && arch.knowledge, `${width}: decision and knowledge paths expected`);

    await page.close();
  }

  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('http://127.0.0.1:5173/login');
  await page.getByLabel('Tên đăng nhập').fill('admin');
  await page.getByLabel('Mật khẩu').fill('admin');
  await page.getByRole('button', { name: /Đăng nhập/ }).click();
  await page.waitForURL(/\/app/);
  await page.locator('.assistant-cta').click();
  await page.locator('.drawer').waitFor();
  assert.equal(await page.locator('.suggestions button:not(.show-more-questions)').count(), 4);
  await page.getByRole('button', { name: 'Xem thêm 10 câu hỏi', exact: true }).click();
  assert.equal(await page.locator('.suggestions button:not(.show-more-questions)').count(), 14);
  await page.getByRole('button', { name: 'CALL và CBS khác nhau thế nào?' }).click();
  await page
    .locator('.drawer .ans-sec')
    .filter({ hasText: 'Nguồn tham khảo' })
    .waitFor({ state: 'visible', timeout: 90000 });
  const drawers = await page.evaluate(() => {
    const d = document.querySelector('.drawer');
    return {
      text: (d && d.innerText) || '',
      stale: (d && d.innerText.includes('Đã lấy quyết định nghiệp vụ')) || false,
      ragFooter: (d && d.innerText.includes('Tra cứu trong kho kiến thức có nguồn tham khảo')) || false,
    };
  });
  assert.ok(!drawers.stale, 'drawer must not show the old decision status');
  assert.ok(drawers.ragFooter, 'drawer must show the RAG footer');
  assert.ok(drawers.text.includes('Nguồn tham khảo'), 'drawer must render Nguồn tham khảo');
  assert.ok(drawers.text.includes('CALL') && drawers.text.includes('CBS'), 'knowledge answer must discuss CALL/CBS');
  knowledgeAnswered = true;
  await page.close();

  assert.ok(knowledgeAnswered, 'live knowledge question must have been answered once');
  console.log('RAG_QA=PASS');
} finally {
  await browser.close();
}