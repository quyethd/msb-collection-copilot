import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true});
const context=await browser.newContext();
const errors=[];const evidence=[];
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
 for(const [width,height] of [[1366,768],[1440,900],[1920,1080]]) {
  const page=await context.newPage();
  await page.setViewportSize({width,height});
  await page.route('https://fonts.googleapis.com/**',r=>r.fulfill({status:200,contentType:'text/css',body:''}));
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error') errors.push(m.text())});
  page.on('request',r=>{if(r.url().includes('/demo/')) assert.equal(r.headers().authorization,undefined)});
  await page.goto('http://127.0.0.1:5173/app');
  await page.locator('.distribution').first().waitFor({timeout:120000});
  const check=async(label)=>{
   assert.equal(await page.locator('nav .active').count(),1);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,label+' overflow');
   const side=await page.locator('.sidebar').boundingBox(),main=await page.locator('main').boundingBox();
   assert.ok(main.x>=side.x+side.width,label+' overlap');
   evidence.push({viewport:`${width}x${height}`,page:label,result:'PASS'});
  };
  await check('overview');assert.equal(await page.locator('.distribution').count(),2);
  const activeColor=await page.locator('nav .active').evaluate(e=>getComputedStyle(e).backgroundColor);
  const priority=page.getByRole('button',{name:'Danh sách ưu tiên',exact:true});
  await priority.hover();const hover=await priority.evaluate(e=>getComputedStyle(e).backgroundColor);assert.notEqual(activeColor,hover);
  await page.mouse.move(width-2,0);assert.notEqual(await priority.evaluate(e=>getComputedStyle(e).backgroundColor),hover);
  await page.screenshot({path:`/tmp/task011e-overview-${width}.png`,fullPage:true});
  await priority.click();await check('priority');assert.equal(await page.locator('th').count(),8);
  const firstCif=await page.locator('tbody tr').first().locator('td').first().innerText();
  await page.getByLabel('Tìm mã khách hàng').fill(firstCif);assert.equal(await page.locator('tbody tr').count(),1);
  await page.locator('tbody button').first().click();await page.locator('.customer-stats').waitFor();
  assert.ok((await page.locator('h1').innerText()).includes(firstCif));
  await priority.click();await page.getByRole('button',{name:'Mở hồ sơ demo SYN002846'}).click();
  await page.locator('.customer-stats').waitFor();await check('customer');
  assert.ok((await page.locator('.customer-stats').innerText()).includes('273.000.000'));
  assert.equal(await page.locator('.decision-card h2').innerText(),'Chờ khách hàng tự thanh toán');
  await page.getByRole('button',{name:'Tạo tình huống thử',exact:true}).click();
  const modal=await page.locator('.scenario-panel').boundingBox();assert.ok(modal.x>=0&&modal.y>=0&&modal.x+modal.width<=width&&modal.y+modal.height<=height);
  assert.ok(Math.abs(modal.x+modal.width/2-width/2)<2);
  await page.getByRole('button',{name:'Xem quyết định thay đổi thế nào'}).click();await page.locator('.scenario-result').waitFor();
  await page.screenshot({path:`/tmp/task011e-scenario-${width}.png`});
  await page.locator('.scenario-head button').click();
  await page.locator('.assistant-cta').click();const drawer=await page.locator('.drawer').boundingBox();assert.ok(drawer.x>=0&&drawer.x+drawer.width<=width&&drawer.height<=height);
  await page.locator('.drawer-head button').click();
  await page.getByRole('button',{name:'Tác động dự kiến',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.impact-cards .stat strong')?.textContent!=='—');await check('impact');
  await page.screenshot({path:`/tmp/task011e-impact-${width}.png`,fullPage:true});
  await page.close();
 }
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({checks:evidence,console_errors:errors,LAYOUT_QA:'PASS'},null,2));
} finally {await browser.close()}
