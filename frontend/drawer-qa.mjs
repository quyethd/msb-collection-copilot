import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const browser = await chromium.launch({ headless: true });
try {
  for (const [width, height] of [[1366, 768], [1440, 900], [1920, 1080]]) {
    const page = await browser.newPage({ viewport: { width, height } });
    await page.goto('http://127.0.0.1:5173/gioi-thieu');
    await page.locator('.so-audience-nav').waitFor();
    await page.locator('.assistant-cta').click();
    await page.locator('.drawer').waitFor();

    const layer = await page.evaluate(() => {
      const nav = document.querySelector('.so-audience-nav');
      const backdrop = document.querySelector('.drawer-backdrop');
      const drawer = document.querySelector('.drawer');
      if (!nav || !backdrop || !drawer) throw new Error('drawer fixture missing');
      const navStyle = getComputedStyle(nav);
      const backdropStyle = getComputedStyle(backdrop);
      const drawerStyle = getComputedStyle(drawer);
      const navBox = nav.getBoundingClientRect();
      const point = document.elementFromPoint(Math.min(innerWidth - 500, navBox.left + navBox.width / 2), navBox.top + navBox.height / 2);
      return {
        navZ: Number(navStyle.zIndex), backdropZ: Number(backdropStyle.zIndex), drawerZ: Number(drawerStyle.zIndex),
        pointIsBackdrop: point === backdrop || backdrop.contains(point),
        navPointerEvents: navStyle.pointerEvents,
      };
    });
    assert.ok(layer.backdropZ > layer.navZ, `${width}: backdrop must cover quick-nav`);
    assert.ok(layer.drawerZ > layer.backdropZ, `${width}: drawer must be above backdrop`);
    assert.equal(layer.pointIsBackdrop, true, `${width}: quick-nav pointer leaked through backdrop`);
    assert.equal(layer.navPointerEvents, 'auto');

    const drawerBox = await page.locator('.drawer').boundingBox();
    const composer = await page.locator('.ask').boundingBox();
    const send = await page.getByRole('button', { name: /Hỏi Trợ lý Thu hồi Nợ/ }).boundingBox();
    assert.ok(drawerBox && drawerBox.y >= 0 && drawerBox.y + drawerBox.height <= height);
    assert.ok(composer && composer.y >= 0 && composer.y + composer.height <= height, `${width}: composer clipped`);
    assert.ok(send && send.y >= 0 && send.y + send.height <= height, `${width}: send button clipped`);

    assert.equal(await page.locator('.suggestions button:not(.show-more-questions)').count(), 4);
    assert.equal(await page.locator('.suggestions-note').innerText(), 'Đây là câu hỏi gợi ý. Bạn vẫn có thể nhập câu hỏi khác.');
    await page.getByRole('button', { name: 'Xem thêm 6 câu hỏi', exact: true }).click();
    assert.equal(await page.locator('.suggestions button:not(.show-more-questions)').count(), 10);
    assert.equal(new Set(await page.locator('.suggestion-group').allTextContents()).size, 4);
    assert.ok(await page.locator('.drawer textarea').isVisible());
    await page.close();
  }
  console.log('DRAWER_QA=PASS');
} finally {
  await browser.close();
}
