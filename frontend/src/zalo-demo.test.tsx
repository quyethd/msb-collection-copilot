// @vitest-environment jsdom
import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import {renderToStaticMarkup} from 'react-dom/server';
import {describe,it,expect,vi,afterEach} from 'vitest';
import {ZaloDemo} from './zalo-demo';

const statusOk=(extra:any={})=>({connection_status:'Đang chờ ghép nối',configured:true,paired:false,worker_alive:true,last_send_state:null,provider:'official-zalo-bot-api',dm_policy_open:'NO',...extra});
const previewOk={text:'☀️ Trợ lý Thu hồi Nợ — Ưu tiên hôm nay'};

function mockFetch(overrides:any={}){
  const fetchMock=vi.fn(async(input:any,init?:any)=>{
    const url=String(input);
    const key=url.split('?')[0];
    if(overrides[key]!==undefined){const value=overrides[key];const isError=typeof value==='number';return {ok:!isError,status:isError?value:200,json:async()=>(isError?{error:{message:'Lỗi mô phỏng'}}:value)}}
    if(key==='/demo/zalo/status')return {ok:true,status:200,json:async()=>statusOk()};
    if(key==='/demo/zalo/preview')return {ok:true,status:200,json:async()=>previewOk};
    return {ok:true,status:200,json:async()=>({})};
  });
  (globalThis as any).fetch=fetchMock;
  return fetchMock;
}

afterEach(()=>{(globalThis as any).fetch=undefined});

describe('ZaloDemo',()=>{
  it('renders the demo heading, quiet pill, and no target or token values',()=>{
    mockFetch({'/demo/zalo/status':statusOk({target_id:'SESSION-NET-1',token:'TOP-SECRET-TOKEN'})});
    const html=renderToStaticMarkup(<ZaloDemo/>);
    expect(html).toContain('Điều khiển Demo Zalo');
    expect(html).toContain('ZALO_DM_POLICY_OPEN=NO');
    expect(html).not.toContain('SESSION-NET-1');
    expect(html).not.toContain('TOP-SECRET-TOKEN');
    expect(html).toContain('Gửi bản tin đầu ngày');
  });
  it('shows waiting state and keeps the send button disabled before pairing',async()=>{
    (globalThis as any).IS_REACT_ACT_ENVIRONMENT=true;
    mockFetch();
    const node=document.createElement('div');document.body.append(node);const root=createRoot(node);
    await act(async()=>root.render(<ZaloDemo/>));
    const html=node.innerHTML;
    expect(html).toContain('Đang chờ người nhận nhắn MSB DEMO');
    expect(html).toContain('Worker đang lắng nghe tin nhắn.');
    expect((node.querySelector('button[disabled]') as HTMLButtonElement)?.textContent).toContain('Gửi bản tin đầu ngày');
    await act(async()=>root.unmount());node.remove();
  });
  it('sends the morning brief when paired',async()=>{
    (globalThis as any).IS_REACT_ACT_ENVIRONMENT=true;
    const fetchMock=mockFetch({'/demo/zalo/status':statusOk({paired:true,connection_status:'Đã kết nối Zalo'})});
    const node=document.createElement('div');document.body.append(node);const root=createRoot(node);
    await act(async()=>root.render(<ZaloDemo/>));
    expect(node.innerHTML).toContain('Đã kết nối Zalo');
    const send=Array.from(node.querySelectorAll('button')).find(b=>b.textContent==='Gửi bản tin đầu ngày') as HTMLButtonElement;
    expect(send.disabled).toBe(false);
    await act(async()=>send.click());
    const posted=fetchMock.mock.calls.filter(([,init])=>(init as any)?.method==='POST').map(([url])=>String(url));
    expect(posted).toContain('/demo/zalo/send-morning-brief');
    expect(node.innerHTML).toContain('Đã gửi bản tin đầu ngày qua Zalo.');
    await act(async()=>root.unmount());node.remove();
  });
  it('requires a second click to reset the recipient',async()=>{
    (globalThis as any).IS_REACT_ACT_ENVIRONMENT=true;
    const fetchMock=mockFetch({'/demo/zalo/reset-recipient':statusOk({configured:false,paired:false,connection_status:'Chưa kết nối'})});
    const node=document.createElement('div');document.body.append(node);const root=createRoot(node);
    await act(async()=>root.render(<ZaloDemo/>));
    const reset=Array.from(node.querySelectorAll('button')).find(b=>b.textContent==='Xoá người nhận') as HTMLButtonElement;
    await act(async()=>reset.click());
    expect(node.innerHTML).toContain('Xác nhận xoá?');
    expect(fetchMock.mock.calls.some(([url])=>String(url)==='/demo/zalo/reset-recipient')).toBe(false);
    await act(async()=>reset.click());
    expect(fetchMock.mock.calls.some(([url])=>String(url)==='/demo/zalo/reset-recipient')).toBe(true);
    expect(node.innerHTML).toContain('Chưa cấu hình người nhận');
    const send=Array.from(node.querySelectorAll('button')).find(b=>b.textContent==='Gửi bản tin đầu ngày') as HTMLButtonElement;
    expect(send.disabled).toBe(true);
    await act(async()=>root.unmount());node.remove();
  });
  it('shows the phone-only recipient form and hides legacy fields',async()=>{
    (globalThis as any).IS_REACT_ACT_ENVIRONMENT=true;
    const fetchMock=mockFetch();
    const node=document.createElement('div');document.body.append(node);const root=createRoot(node);
    await act(async()=>root.render(<ZaloDemo/>));
    const html=node.innerHTML;
    expect(html).toContain('Số điện thoại');
    expect(html).not.toContain('Nhãn demo');
    expect(html).not.toContain('Tên hiển thị');
    expect((html.match(/<label>Số điện thoại/g)||[]).length).toBe(1);
    await act(async()=>root.unmount());node.remove();
  });
  it('saves the recipient with only the phone field',async()=>{
    (globalThis as any).IS_REACT_ACT_ENVIRONMENT=true;
    const fetchMock=mockFetch();
    const node=document.createElement('div');document.body.append(node);const root=createRoot(node);
    await act(async()=>root.render(<ZaloDemo/>));
    const input=node.querySelector('input') as HTMLInputElement;
    const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value')?.set;
    await act(async()=>{setter?.call(input,'0912 345 678');input.dispatchEvent(new Event('input',{bubbles:true}))});
    const save=Array.from(node.querySelectorAll('button')).find(b=>b.textContent==='Lưu người nhận') as HTMLButtonElement;
    await act(async()=>save.click());
    const recipientCall=fetchMock.mock.calls.find(([url])=>String(url)==='/demo/zalo/recipient');
    expect(recipientCall).toBeTruthy();
    const payload=JSON.parse((recipientCall as any)[1].body);
    expect(payload.display_phone).toBe('0912 345 678');
    expect(payload).not.toHaveProperty('demo_label');
    expect(payload).not.toHaveProperty('display_name');
    await act(async()=>root.unmount());node.remove();
  });
  it('does not render technical target id on save or connected state',async()=>{
    (globalThis as any).IS_REACT_ACT_ENVIRONMENT=true;
    mockFetch({'/demo/zalo/status':statusOk({paired:true,connection_status:'Đã kết nối Zalo',target_id:'SESSION-NET-9'})});
    const node=document.createElement('div');document.body.append(node);const root=createRoot(node);
    await act(async()=>root.render(<ZaloDemo/>));
    expect(node.innerHTML).toContain('Đã kết nối Zalo');
    expect(node.innerHTML).not.toContain('SESSION-NET-9');
    await act(async()=>root.unmount());node.remove();
  });
});