import React,{useEffect,useState} from 'react';

async function call(path:string,init?:RequestInit){const r=await fetch(path,{...init,credentials:'include',headers:{'Content-Type':'application/json',...(init?.headers||{})}});let b:any={};try{b=await r.json()}catch{/* non-json response */}if(!r.ok||b.error)throw new Error(b.error?.message||'Không thể thực hiện thao tác Zalo');return b}

const EMPTY:string='';

export function ZaloDemo(){
  const [form,setForm]=useState({display_phone:''});
  const [state,setState]=useState<any>();
  const [brief,setBrief]=useState<any>();
  const [message,setMessage]=useState(EMPTY);
  const [busy,setBusy]=useState(false);
  const [confirmingReset,setConfirmingReset]=useState(false);
  const load=()=>call('/demo/zalo/status').then(setState).catch(e=>setMessage(e.message));
  useEffect(()=>{load();call('/demo/zalo/preview').then(setBrief).catch(()=>{});const timer=setInterval(load,10000);return ()=>{clearInterval(timer)}},[],);
  const notify=(text:string)=>{setMessage(text);setConfirmingReset(false)};
  const configure=async()=>{setMessage(EMPTY);try{setState(await call('/demo/zalo/recipient',{method:'POST',body:JSON.stringify(form)}));notify('Đã lưu người nhận. Người nhận mở bot Zalo và gửi MSB DEMO để ghép nối.')}catch(e:any){setMessage(e.message)}};
  const send=async()=>{if(busy||!state?.paired)return;setBusy(true);setMessage(EMPTY);try{await call('/demo/zalo/send-morning-brief',{method:'POST',body:'{}'});notify('Đã gửi bản tin đầu ngày qua Zalo.')}catch(e:any){setMessage(e.message)}finally{setBusy(false)}};
  const reset=async()=>{if(!confirmingReset){setConfirmingReset(true);return}if(busy)return;setBusy(true);setMessage(EMPTY);try{setState(await call('/demo/zalo/reset-recipient',{method:'POST',body:'{}'}));notify('Đã xoá người nhận.')}catch(e:any){setMessage(e.message)}finally{setBusy(false);setConfirmingReset(false)}};
  const statusText = state?.configured ? (state?.paired ? 'Đã kết nối Zalo' : 'Đang chờ người nhận nhắn MSB DEMO') : 'Chưa cấu hình người nhận';
  const workerOnline = state?.worker_alive;
  const blocked = ['Lỗi gửi'].includes(state?.last_send_state);
  return <section className="content zalo-page"><div className="page-title"><div><div className="eyebrow">HACKATHON · KÊNH ZALO</div><h1>Điều khiển Demo Zalo</h1><p>Gửi thủ công một bản tin tổng hợp từ dữ liệu mô phỏng và Decision Core hiện có. Không có lịch tự động gửi.</p></div><span className="demo-pill">ZALO_DM_POLICY_OPEN=NO</span></div><div className="zalo-grid">
  <div className="panel">
    <div className="panel-head"><div><h2>Người nhận demo</h2><p>Số điện thoại hiển thị (chỉ là nhãn tham chiếu, không dùng để gửi).</p></div><span className={`worker-dot${workerOnline?' on':' off'}`} title={workerOnline?'Zalo worker đang lắng nghe':'Zalo worker chưa hoạt động'}/></div>
    <div className="zalo-form"><label>Số điện thoại<input value={form.display_phone} onChange={e=>setForm({...form,display_phone:e.target.value})}/></label></div>
    <div className="zalo-actions"><button className="primary" onClick={configure}>Lưu người nhận</button><button className="outline" onClick={reset} disabled={busy||!state?.configured}>{confirmingReset?'Xác nhận xoá?':'Xoá người nhận'}</button></div>
    <div className="zalo-status"><span>Trạng thái kết nối</span><b>{statusText}</b>{!workerOnline&&<small className="worker-note">Worker chưa hoạt động — tin nhắn Zalo sẽ không được xử lý.</small>}{workerOnline&&<small>Worker đang lắng nghe tin nhắn.</small>}</div>
  </div>
  <div className="panel">
    <div className="panel-head"><div><h2>Bản tin đầu ngày</h2><p>Bản xem trước được tính deterministic từ portfolio + NBA hiện có, không dùng LLM để chọn khách hàng.</p></div>{state?.paired&&<span className={`event-stamp${blocked?' send-error':''}`}>{state.last_send_state||'Sẵn sàng gửi'}</span>}</div>
    <pre className="zalo-preview">{brief?.text||'Đang tải bản xem trước…'}</pre>
    <div className="zalo-actions"><button className="primary" disabled={busy||!state?.paired} onClick={send}>{busy?'Đang gửi…':'Gửi bản tin đầu ngày'}</button></div>
    <p className="assumption-note zalo-hint">Nút gửi chỉ hoạt động sau khi người nhận đã ghép nối (gửi MSB DEMO trong Zalo).</p>
    {message&&<p role="status" className="assistant-status">{message}</p>}
  </div>
  </div><div className="panel zalo-flow"><h2>Ghép nối an toàn</h2><p>Người nhận mở bot Zalo chính thức và gửi <b>MSB DEMO</b>; target ID được bind từ inbound interaction được chấp thuận. Người chưa ghép nối không nhận bất kỳ thông tin danh mục; dữ liệu demo là mô phỏng.</p></div></section>
}