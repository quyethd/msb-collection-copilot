import { FormEvent, useEffect, useState } from 'react';
import { ArrowRight, LoaderCircle, LogIn, LogOut, ShieldCheck } from 'lucide-react';
import { SystemOverviewPage } from './pages/system-overview/SystemOverviewPage';

export function PublicLanding() {
  useEffect(() => {
    if (window.location.pathname === '/gioi-thieu') window.history.replaceState({}, '', '/');
  }, []);
  const goLogin = () => { window.location.href = '/login'; };
  return <div className="public-site">
    <header className="public-header">
      <a className="public-brand" href="/" aria-label="MSB Trợ lý Thu hồi Nợ">
        <span className="public-brand-mark">MSB</span>
        <span><b>Trợ lý Thu hồi Nợ</b><small>Powered by GreenNode AI</small></span>
      </a>
      <a className="public-login-link" href="/login"><LogIn size={16}/> Đăng nhập hệ thống</a>
    </header>
    <SystemOverviewPage onOpenOverview={goLogin} onOpenCustomer={goLogin} heroPrimaryHref="#benefits" heroPrimaryLabel="Khám phá giải pháp" ctaOverviewLabel="Đăng nhập hệ thống" ctaCustomerLabel="Xem bản demo" />
  </div>;
}

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { fetch('/demo/auth/me', { credentials: 'include' }).then(r => { if (r.ok) window.location.replace('/app'); }); }, []);
  const submit = async (event: FormEvent) => {
    event.preventDefault(); if (busy) return; setBusy(true); setError('');
    try {
      const response = await fetch('/demo/auth/login', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username, password}) });
      const body = await response.json();
      if (!response.ok) throw new Error(body?.error?.message || 'Không thể đăng nhập.');
      const next = new URLSearchParams(window.location.search).get('next');
      window.location.replace(next && next.startsWith('/app') ? next : '/app');
    } catch (e: any) { setError(e.message || 'Không thể đăng nhập.'); setBusy(false); }
  };
  return <main className="login-page">
    <a className="login-brand" href="/"><span className="public-brand-mark">MSB</span><span><b>Trợ lý Thu hồi Nợ</b><small>Powered by GreenNode AI</small></span></a>
    <section className="login-card" aria-labelledby="login-title">
      <div className="login-icon"><ShieldCheck size={21}/></div><div className="eyebrow">KHU VỰC TÁC NGHIỆP</div>
      <h1 id="login-title">Đăng nhập hệ thống</h1><p>Truy cập Tổng quan, danh sách ưu tiên và hồ sơ khách hàng trong bản demo.</p>
      <form onSubmit={submit}><label>Tên đăng nhập<input value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username" required /></label><label>Mật khẩu<input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password" required /></label>{error&&<p className="login-error" role="alert">{error}</p>}<button className="primary login-submit" disabled={busy}>{busy?<><LoaderCircle className="spin" size={16}/> Đang đăng nhập...</>:<>Đăng nhập <ArrowRight size={16}/></>}</button></form>
      <small className="login-disclaimer">Đây là quyền truy cập bản demo, không phải xác thực ngân hàng trong môi trường sản xuất.</small>
    </section>
    <footer className="login-footer">MSB · Powered by GreenNode AI · Dữ liệu mô phỏng</footer>
  </main>;
}

export function LogoutButton({logout}:{logout:()=>void}) { return <button className="logout-button" onClick={logout}><LogOut size={16}/> Đăng xuất</button>; }
