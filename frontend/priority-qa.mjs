import {chromium} from 'playwright';
import assert from 'node:assert/strict';

const browser=await chromium.launch({headless:true});
const context=await browser.newContext();
const results=[];
async function login(page) {
  await page.goto('http://127.0.0.1:5173/login');
  await page.getByLabel('Tên đăng nhập').fill('admin');
  await page.getByLabel('Mật khẩu').fill('admin');
  await page.getByRole('button',{name:/Đăng nhập/}).click();
  await page.waitForURL(/\/app/);
}
try {
  const loginPage=await context.newPage();
  await login(loginPage);
  await loginPage.close();
  for (const [width,height] of [[1366,768],[1440,900],[1920,1080]]) {
    const page=await context.newPage();
    await page.setViewportSize({width,height});
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error') errors.push(m.text())});
    await page.goto('http://127.0.0.1:5173/app');
    await page.getByRole('button',{name:'Danh sách ưu tiên',exact:true}).click();
    await page.locator('.priority-page tbody tr').first().waitFor({timeout:120000});
    assert.equal(await page.locator('th').count(),8);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`${width}: page overflow`);
    assert.equal(await page.locator('.priority-page .table-wrap').evaluate(e=>e.scrollWidth<=e.clientWidth),true,`${width}: table overflow`);
    assert.ok(await page.locator('.priority-page td:nth-child(7)').first().getAttribute('title'));
    await page.screenshot({path:`/tmp/task011g-priority-${width}.png`,fullPage:true});

    const rows=page.locator('.priority-page tbody tr');
    const first=await rows.nth(0).locator('td').first().innerText();
    const second=await rows.nth(1).locator('td').first().innerText();
    await rows.nth(0).click({button:'right'});
    assert.equal(await page.getByRole('menu').count(),1);
    assert.ok((await page.getByRole('menu').innerText()).includes('Xem chi tiết khách hàng'));
    await page.keyboard.press('Escape');
    assert.equal(await page.getByRole('menu').count(),0);
    await rows.nth(1).click({button:'right'});
    await page.getByRole('menuitem').click();
    assert.ok((await page.locator('h1').innerText()).includes(second));
    await page.getByRole('button',{name:'Danh sách ưu tiên',exact:true}).click();
    await page.locator('.priority-page tbody tr').first().waitFor();
    await page.locator('.priority-page tbody tr').nth(1).dblclick();
    assert.ok((await page.locator('h1').innerText()).includes(second));
    await page.getByRole('button',{name:'Danh sách ưu tiên',exact:true}).click();
    await page.locator('.priority-page tbody tr').first().waitFor();
    await page.locator('.priority-page tbody tr').nth(0).focus();
    await page.keyboard.press('Enter');
    assert.ok((await page.locator('h1').innerText()).includes(first));
    await page.getByRole('button',{name:'Danh sách ưu tiên',exact:true}).click();
    await page.locator('.priority-page tbody tr').first().waitFor();
    await page.locator('.priority-detail').first().click();
    assert.ok((await page.locator('h1').innerText()).includes(first));
    await page.getByRole('button',{name:'Danh sách ưu tiên',exact:true}).click();
    await page.locator('.priority-page tbody tr').first().waitFor();
    await page.getByLabel('Tìm mã khách hàng').fill(first);
    assert.equal(await page.locator('.priority-page tbody tr').count(),1);
    assert.deepEqual(errors,[]);
    results.push({viewport:`${width}x${height}`,horizontal_scroll:'NO',row_context_menu:'PASS',double_click:'PASS',keyboard_enter:'PASS',detail_icon:'PASS',filters:'PASS'});
    await page.close();
  }
  console.log(JSON.stringify({results,PRIORITY_REASON_COLUMN:'PASS',TESTS:'PASS'},null,2));
} finally {await browser.close()}
