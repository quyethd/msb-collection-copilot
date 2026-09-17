import React, {useEffect, useState} from 'react';
import {Activity, ArrowRight, BarChart3, ChevronDown, ChevronRight, LayoutDashboard, LogOut, MessageCircle, Radio, ShieldCheck, UserRound} from 'lucide-react';

export type Page = string;
export const primaryNav = [
  {page:'overview', label:'Tổng quan', icon:LayoutDashboard},
  {page:'priority', label:'Danh sách ưu tiên', icon:Activity},
  {page:'customer', label:'Khách hàng', icon:UserRound},
] as const;
export const adminNav = [
  {page:'impact', label:'Tác động dự kiến', icon:BarChart3},
  {page:'zalo', label:'Điều khiển Demo Zalo', icon:Radio},
] as const;
const routeLabel = (route:string) => ({CALL:'Tác nghiệp CALL', CBS:'Tác nghiệp CBS'}[route] || 'Khác');
const actionLabel = (action:string) => ({WAIT:'Chờ theo dõi',WAIT_SELF_CURE:'Chờ khách hàng tự thanh toán',CONTACT:'Liên hệ khách hàng',REMIND:'Nhắc thanh toán',PTP_FOLLOW_UP:'Theo dõi cam kết',PTP_RECOVERY:'Xử lý cam kết không thực hiện',PARTIAL_PAYMENT:'Theo dõi thanh toán một phần',CALLBACK:'Gọi lại theo lịch',VERIFY_CONTACT:'Xác minh liên hệ',ESCALATE:'Chuyển mức xử lý'}[action] || 'Chưa có đề xuất');
const money = (n:number) => new Intl.NumberFormat('vi-VN').format(n) + ' đ';
export function Sidebar({page,cif,setPage,open,setCopilot,logout}:any) {
  const isAdminChild = adminNav.some((x:any)=>x.page===page);
  const [adminOpen,setAdminOpen] = useState(isAdminChild);
  useEffect(()=>{ if(isAdminChild) setAdminOpen(true); },[isAdminChild]);
  return <aside className="sidebar"><a className="brand" href="/" aria-label="Về trang giới thiệu MSB Trợ lý Thu hồi Nợ"><div className="msb">MSB</div><div><b>Trợ lý Thu hồi Nợ</b><span>Powered by GreenNode AI</span></div></a>
    <nav aria-label="Điều hướng chính">{primaryNav.map(({page:target,label,icon:Icon}:any) => <button key={target} className={`navitem${page===target?' active':''}`} aria-current={page===target?'page':undefined} onClick={()=>target==='customer'?open(cif):setPage(target)}><Icon size={18}/><span>{label}</span></button>)}
    <div className="sidebar-separator admin-separator"/>
    <button className={`navitem admin-toggle${adminOpen?' admin-open':''}`} aria-expanded={adminOpen} onClick={()=>setAdminOpen(!adminOpen)}><BarChart3 size={18}/><span>Quản trị</span>{adminOpen?<ChevronDown size={16}/>:<ChevronRight size={16}/>}</button>
    {adminOpen && <div className="admin-children">{adminNav.map(({page:target,label,icon:Icon}:any) => <button key={target} className={`navitem admin-child${page===target?' active':''}`} aria-current={page===target?'page':undefined} onClick={()=>setPage(target)}><Icon size={16}/><span>{label}</span></button>)}</div>}
    </nav>
    <div className="sidebar-separator assistant-separator"/>
    <button className="assistant-cta" onClick={()=>setCopilot(true)}><MessageCircle size={19}/><span><b>Trợ lý Thu hồi Nợ</b><small>Hỏi về quyết định</small></span><ArrowRight size={15}/></button>
    {logout&&<button className="logout-button" onClick={logout}><LogOut size={16}/> Đăng xuất</button>}
    <div className="side-foot"><ShieldCheck size={15}/> Môi trường demo<br/><span>Dữ liệu mô phỏng</span></div></aside>;
}
export function Header({page}:{page:Page}) {return <header><div className="crumb">MSB / {page==='system-overview'?'Giới thiệu hệ thống':primaryNav.find(x=>x.page===page)?.label || adminNav.find((x:any)=>x.page===page)?.label}</div><div className="header-right"><span className="live"><i/> Môi trường mô phỏng</span><div className="avatar">HT</div></div></header>}
export function chartCounts(rows:any[], kind:'action'|'route') {
  const counts:Record<string,number> = {};
  for(const row of rows) {
    const treatment = row.nba?.treatment;
    const label = kind==='route' ? routeLabel(row.final_route) : !treatment ? 'Chưa có đề xuất' : ['WAIT','WAIT_SELF_CURE'].includes(treatment) ? 'Chờ / Chờ tự thanh toán' : ['PTP_FOLLOW_UP','PTP_RECOVERY','PARTIAL_PAYMENT'].includes(treatment) ? 'Theo dõi cam kết' : ['CONTACT','CALLBACK','VERIFY_CONTACT'].includes(treatment) ? 'Liên hệ' : treatment==='REMIND' ? 'Nhắc thanh toán' : 'Khác';
    counts[label] = (counts[label] || 0) + 1;
  }
  return Object.entries(counts);
}
function Distribution({title,counts,total}:{title:string,counts:[string,number][],total:number}) {
  return <section className="panel distribution" aria-label={title}><h2>{title}</h2><p>Trong {total} khách hàng được API trả về</p>{counts.length ? <ul>{counts.map(([label,count])=><li key={label}><div><span>{label}</span><b>{count}</b></div><div className="chart-track"><span style={{width:`${count/total*100}%`}}/></div></li>)}</ul>:<p>Chưa có dữ liệu.</p>}</section>;
}
export function Overview({portfolio,summary,open,loading}:{portfolio:any[],summary:any,open:(cif:string)=>void,loading:boolean}) {
  const cards = [['Tổng khách hàng',summary.portfolio_size],['Danh mục được trả về',portfolio.length],['Thuộc tuyến CALL',summary.call_route_count],['Có quyết định',summary.decisions_available]];
  return <section className="content overview-page"><div className="page-title"><div><div className="eyebrow">TỔNG QUAN</div><h1>Toàn cảnh danh mục thu hồi hôm nay</h1><p>Dữ liệu mô phỏng · Phân bổ bên dưới chỉ phản ánh các hồ sơ được API trả về.</p></div></div><div className="stat-grid">{cards.map(([label,count])=><div className="stat overview-stat" key={label}><span>{label}</span><strong>{count??'—'}</strong></div>)}</div>{loading?<p role="status">Đang tải quyết định danh mục…</p>:<><div className="overview-charts"><Distribution title="Phân bổ hành động hôm nay" counts={chartCounts(portfolio,'action')} total={portfolio.length}/><Distribution title="Phân bổ tuyến xử lý" counts={chartCounts(portfolio,'route')} total={portfolio.length}/></div><section className="panel overview-alerts"><h2>Điểm cần chú ý hôm nay</h2><p>Trong danh mục được trả về: {portfolio.filter(x=>x.hard_suppressed).length} hồ sơ có hạn chế liên hệ; {portfolio.filter(x=>x.nba?.channel==='NONE').length} hồ sơ chưa cần liên hệ theo đề xuất hiện tại.</p><button className="outline" onClick={()=>open('SYN002846')}>Xem khách hàng SYN002846 <ArrowRight size={15}/></button></section></>}</section>;
}
export function Priority({portfolio,open,loading}:{portfolio:any[],open:(cif:string)=>void,loading:boolean}) {
  const [search,setSearch]=useState(''), [route,setRoute]=useState(''), [action,setAction]=useState(''), [menu,setMenu]=useState<{cif:string,x:number,y:number}|null>(null);
  const rows=portfolio.filter(x=>x.cif.toLowerCase().includes(search.trim().toLowerCase())&&(!route||x.final_route===route)&&(!action||x.nba?.treatment===action));
  useEffect(()=>{const close=()=>setMenu(null);const escape=(e:KeyboardEvent)=>{if(e.key==='Escape')close()};document.addEventListener('click',close);document.addEventListener('keydown',escape);return()=>{document.removeEventListener('click',close);document.removeEventListener('keydown',escape)}},[]);
  const showMenu=(event:React.MouseEvent<HTMLTableRowElement>,cif:string)=>{event.preventDefault();const x=Math.min(event.clientX,window.innerWidth-220),y=Math.min(event.clientY,window.innerHeight-55);setMenu({cif,x:Math.max(8,x),y:Math.max(8,y)})};
  const openDetail=(cif:string)=>{setMenu(null);open(cif)};
  return <section className="content priority-page"><div className="page-title"><div><div className="eyebrow">DANH SÁCH ƯU TIÊN</div><h1>Danh sách khách hàng ưu tiên hôm nay</h1><p>Xác định khách hàng nên xử lý trước dựa trên cơ hội thu hồi và hành động được đề xuất.</p></div></div><div className="priority-filters"><label>Tìm mã khách hàng<input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Tìm CIF trong danh sách"/></label><label>Tuyến xử lý<select value={route} onChange={e=>setRoute(e.target.value)}><option value="">Tất cả tuyến</option>{[...new Set(portfolio.map(x=>x.final_route))].map(x=><option key={x} value={x}>{routeLabel(x)}</option>)}</select></label><label>Hành động đề xuất<select value={action} onChange={e=>setAction(e.target.value)}><option value="">Tất cả hành động</option>{[...new Set(portfolio.map(x=>x.nba?.treatment).filter(Boolean))].map(x=><option key={x} value={x}>{actionLabel(x)}</option>)}</select></label></div><p className="scope-note">Giữ thứ tự xếp hạng hiện có · {rows.length} / {portfolio.length} hồ sơ API trả về. <button className="link" onClick={()=>open('SYN002846')}>Mở hồ sơ demo SYN002846</button></p>{loading?<p role="status">Đang tải quyết định danh mục…</p>:<div className="panel table-wrap" role="region" aria-label="Danh sách khách hàng ưu tiên"><table><thead><tr>{['Mã khách hàng','Dư nợ','Quá hạn','Điểm cơ hội thu hồi','Tuyến xử lý','Hành động đề xuất','Lý do chính','Chi tiết'].map(x=><th key={x}>{x}</th>)}</tr></thead><tbody>{rows.map(x=><tr key={x.cif} tabIndex={0} aria-label={`Khách hàng ${x.cif}`} onKeyDown={e=>{if(e.key==='Enter')openDetail(x.cif)}} onDoubleClick={()=>openDetail(x.cif)} onContextMenu={e=>showMenu(e,x.cif)}><td><button className="priority-cif link" aria-label={`Xem chi tiết ${x.cif}`} onClick={()=>openDetail(x.cif)}>{x.cif}</button></td><td>{money(x.total_outstanding_cif)}</td><td>{x.max_dpd_cif} ngày</td><td>{x.recovery_opportunity_score}</td><td>{routeLabel(x.final_route)}</td><td>{actionLabel(x.nba?.treatment)}</td><td title={`Quá hạn ${x.max_dpd_cif} ngày · Điểm cơ hội ${x.recovery_opportunity_score}`}>Quá hạn {x.max_dpd_cif} ngày · Điểm cơ hội {x.recovery_opportunity_score}</td><td><button className="priority-detail link" aria-label={`Xem chi tiết ${x.cif}`} title={`Xem chi tiết ${x.cif}`} onClick={()=>openDetail(x.cif)}><ChevronRight size={17}/></button></td></tr>)}</tbody></table>{!rows.length&&<p className="empty">Không có hồ sơ phù hợp trong danh sách.</p>}</div>}{menu&&<div className="priority-context-menu" role="menu" style={{left:menu.x,top:menu.y}} onClick={e=>e.stopPropagation()}><button role="menuitem" onClick={()=>openDetail(menu.cif)}>Xem chi tiết khách hàng</button></div>}</section>;
}
