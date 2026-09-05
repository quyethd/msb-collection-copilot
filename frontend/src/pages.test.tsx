// @vitest-environment jsdom
import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import {renderToStaticMarkup} from 'react-dom/server';
import {describe,it,expect,vi} from 'vitest';
import {Sidebar,Overview,Priority,primaryNav,chartCounts} from './pages';
const rows=[{cif:'SYN002846',total_outstanding_cif:273000000,max_dpd_cif:11,recovery_opportunity_score:47,final_route:'CALL',nba:{treatment:'WAIT_SELF_CURE',channel:'NONE'}},{cif:'SYN000001',total_outstanding_cif:100,max_dpd_cif:20,recovery_opportunity_score:50,final_route:'CBS',nba:{treatment:'CONTACT',channel:'CALL'}}];
describe('Final primary navigation',()=>{
  it('contains exactly the four real operational pages',()=>{
    expect(primaryNav.map(x=>x.page)).toEqual(['overview','priority','customer','impact']);
    expect(primaryNav.map(x=>x.label)).toEqual(['Tổng quan','Danh sách ưu tiên','Khách hàng','Tác động dự kiến']);
  });
  for(const page of primaryNav.map(x=>x.page)) it(`only ${page} is active`,()=>{
    const html=renderToStaticMarkup(<Sidebar page={page}/>);
    const node=document.createElement('div');node.innerHTML=html;
    expect(node.querySelectorAll('nav button')).toHaveLength(4);
    expect(node.querySelectorAll('nav [aria-current="page"]')).toHaveLength(1);
    expect(node.querySelector('nav [aria-current="page"]')?.textContent).toBe(primaryNav.find(x=>x.page===page)?.label);
    expect(node.querySelector('.assistant-cta.active')).toBeNull();
    expect(node.querySelector('.sidebar-secondary-slot')?.children).toHaveLength(0);
    for(const text of ['Cảnh báo sớm','Cam kết thanh toán','Lịch sử liên hệ','Giới thiệu hệ thống']) expect(node.querySelector('nav')?.textContent).not.toContain(text);
  });
  it('overview has two actual-data charts and no priority table',()=>{
    const html=renderToStaticMarkup(<Overview portfolio={rows} summary={{}} open={()=>{}} loading={false}/>);
    expect(html.match(/class="panel distribution"/g)).toHaveLength(2);
    expect(html).toContain('Phân bổ hành động hôm nay');expect(html).toContain('Phân bổ tuyến xử lý');
    expect(html).toContain('Điểm cần chú ý hôm nay');expect(html).not.toContain('<table');
    expect(chartCounts(rows,'action')).toEqual([['Chờ / Chờ tự thanh toán',1],['Liên hệ',1]]);
    expect(chartCounts(rows,'route')).toEqual([['Tác nghiệp CALL',1],['Tác nghiệp CBS',1]]);
    expect(chartCounts([],'action')).toEqual([]);
  });
  it('priority is independent and detail selects the row CIF',async()=>{
    (globalThis as any).IS_REACT_ACT_ENVIRONMENT=true;
    const node=document.createElement('div');document.body.append(node);const root=createRoot(node);const open=vi.fn();
    await act(async()=>root.render(<Priority portfolio={rows} open={open} loading={false}/>));
    expect(node.querySelectorAll('th')).toHaveLength(8);expect(node.querySelectorAll('.distribution')).toHaveLength(0);
    expect(node.querySelectorAll('input')).toHaveLength(1);expect(node.querySelectorAll('select')).toHaveLength(2);
    await act(async()=>(node.querySelector('tbody button') as HTMLButtonElement).click());
    expect(open).toHaveBeenCalledWith('SYN002846');
    const select=node.querySelector('select')!;
    await act(async()=>{select.value='CBS';select.dispatchEvent(new Event('change',{bubbles:true}))});
    expect(node.querySelectorAll('tbody tr')).toHaveLength(1);expect(node.querySelector('tbody')?.textContent).toContain('SYN000001');
    await act(async()=>root.unmount());node.remove();
  });
});
