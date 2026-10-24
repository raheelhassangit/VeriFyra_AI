import React from "react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ShieldCheck, ArrowRight, Eye, EyeOff, LockKeyhole, Mail, UserRound } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { getErrorMessage } from "../api/client";

export default function Auth({ mode = "login" }) {
  const isRegister = mode === "register";
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try {
      if (isRegister) {
        await register(form);
        await login(form.email, form.password);
      } else await login(form.email, form.password);
      navigate("/app");
    } catch (err) { setError(getErrorMessage(err)); }
    finally { setBusy(false); }
  };
  return <div className="auth-layout"><section className="auth-story"><div className="brand brand-light"><div className="brand-mark"><ShieldCheck size={22}/></div><div><b>VeriFyra</b><small>TRUST INTELLIGENCE</small></div></div><div className="story-copy"><span className="eyebrow"><span className="live-dot"/> MULTI-AGENT VERIFICATION</span><h1>Trust what you<br/><em>can verify.</em></h1><p>One workspace to inspect software projects, orchestrate AI audits, and turn evidence into confident decisions.</p><div className="story-stats"><div><b>04</b><span>Intelligence layers</span></div><div><b>01</b><span>Evidence-led verdict</span></div></div></div><div className="story-footer">BUILT FOR TRANSPARENCY <span>·</span> POWERED BY EVIDENCE</div></section><section className="auth-panel"><div className="auth-card"><div className="auth-mobile-brand"><ShieldCheck/> VeriFyra</div><div className="auth-icon"><LockKeyhole size={22}/></div><div className="eyebrow">{isRegister ? "CREATE YOUR ACCOUNT" : "WELCOME BACK"}</div><h2>{isRegister ? "Join VeriFyra" : "Sign in to your workspace"}</h2><p className="muted">{isRegister ? "Create an account to start verifying your projects." : "Your evidence and audits are right where you left them."}</p>{error && <div className="alert error">{error}</div>}<form onSubmit={submit} className="auth-form">{isRegister && <label>Full name<div className="input-wrap"><UserRound size={17}/><input name="full_name" value={form.full_name} onChange={change} placeholder="Your full name" required autoComplete="name"/></div></label>}<label>Email address<div className="input-wrap"><Mail size={17}/><input type="email" name="email" value={form.email} onChange={change} placeholder="you@company.com" required autoComplete="email"/></div></label><label>Password<div className="input-wrap"><LockKeyhole size={17}/><input type={showPassword ? "text" : "password"} name="password" value={form.password} onChange={change} placeholder={isRegister ? "At least 10 characters" : "Enter your password"} minLength={isRegister ? 10 : undefined} required autoComplete={isRegister ? "new-password" : "current-password"}/><button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)} aria-label="Toggle password visibility">{showPassword ? <EyeOff size={17}/> : <Eye size={17}/>}</button></div></label><button className="btn btn-primary btn-wide" disabled={busy}>{busy ? "Please wait…" : isRegister ? "Create account" : "Sign in"} {!busy && <ArrowRight size={17}/>}</button></form><div className="auth-switch">{isRegister ? "Already have an account?" : "New to VeriFyra?"} <Link to={isRegister ? "/login" : "/register"}>{isRegister ? "Sign in" : "Create account"}</Link></div><div className="auth-footnote"><LockKeyhole size={14}/> Protected with token-based authentication</div></div></section></div>;
}