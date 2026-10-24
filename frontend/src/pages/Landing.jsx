import React from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, FileSearch, GitBranch, BrainCircuit, ArrowRight, CheckCircle2, Search, Scale } from "lucide-react";

export default function Landing() {
  return <div className="landing-page">
    <header className="landing-navbar">
      <Link to="/" className="landing-brand"><span className="landing-logo"><ShieldCheck size={23}/></span><span>VeriFyra<span className="brand-accent"> AI</span></span></Link>
      <nav className="landing-nav-links"><a href="#features">Features</a><a href="#how-it-works">How it works</a><Link to="/login">Sign in</Link><Link to="/register" className="landing-nav-cta">Get started <ArrowRight size={15}/></Link></nav>
      <Link to="/register" className="landing-mobile-cta">Get started <ArrowRight size={15}/></Link>
    </header>
    <main>
      <section className="landing-hero"><div className="landing-hero-copy">
        <div className="landing-eyebrow"><span className="status-dot"/> AI-ASSISTED VERIFICATION</div>
        <h1>Trust every claim.<br/><span>Verify every signal.</span></h1>
        <p className="landing-hero-description">Bring project details, repository signals, and supporting documents into one structured verification workflow. Review the evidence, understand the findings, and make better-informed decisions.</p>
        <div className="landing-hero-actions"><Link to="/register" className="landing-primary-button">Start verifying <ArrowRight size={17}/></Link><Link to="/login" className="landing-secondary-button">Sign in to workspace</Link></div>
        <div className="landing-trust-note"><CheckCircle2 size={16}/> Evidence-focused analysis. Findings you can review.</div>
      </div><div className="landing-visual"><div className="verification-card">
        <div className="verification-card-top"><div><span className="preview-label">VERIFICATION WORKSPACE</span><h3>Analysis overview</h3></div><span className="preview-icon"><ShieldCheck size={22}/></span></div>
        <div className="preview-project"><span className="preview-project-icon"><GitBranch size={20}/></span><div className="preview-project-info"><strong>Project verification</strong><span>Repository and evidence review</span></div><span className="preview-live-dot"/></div>
        <div className="preview-divider"/><span className="preview-label">REVIEW WORKFLOW</span>
        <div className="pipeline-step"><span className="pipeline-icon"><GitBranch size={17}/></span><div className="pipeline-text"><strong>Repository analysis</strong><span>Inspect available project signals</span></div><CheckCircle2 size={17} className="pipeline-check"/></div>
        <div className="pipeline-step"><span className="pipeline-icon"><FileSearch size={17}/></span><div className="pipeline-text"><strong>Document review</strong><span>Compare claims with supplied evidence</span></div><CheckCircle2 size={17} className="pipeline-check"/></div>
        <div className="pipeline-step"><span className="pipeline-icon"><BrainCircuit size={17}/></span><div className="pipeline-text"><strong>Evidence assessment</strong><span>Collect findings for human review</span></div><span className="pipeline-pending">Review</span></div>
        <div className="preview-footer"><ShieldCheck size={17}/> Structured analysis, transparent review</div>
      </div><div className="floating-chip chip-top"><Search size={15}/> Evidence-first analysis</div><div className="floating-chip chip-bottom"><Scale size={16}/> Reviewable findings</div></div></section>
      <section className="landing-feature-strip"><div><span className="feature-strip-icon"><GitBranch size={19}/></span><div><strong>Repository intelligence</strong><span>Explore technical signals</span></div></div><div><span className="feature-strip-icon"><FileSearch size={19}/></span><div><strong>Document review</strong><span>Inspect supporting material</span></div></div><div><span className="feature-strip-icon"><BrainCircuit size={19}/></span><div><strong>Multi-agent workflow</strong><span>Structured analysis stages</span></div></div><div><span className="feature-strip-icon"><ShieldCheck size={19}/></span><div><strong>Evidence-led decisions</strong><span>Findings ready for review</span></div></div></section>
      <section className="landing-features" id="features"><div className="landing-section-heading"><span className="landing-eyebrow">BUILT FOR BETTER DECISIONS</span><h2>Verification with more clarity.</h2><p>A practical workspace for bringing technical signals and supporting information together.</p></div><div className="landing-feature-grid"><article className="landing-feature-card"><span className="landing-feature-icon"><GitBranch size={22}/></span><h3>Repository analysis</h3><p>Examine submitted repositories and available project information for relevant technical signals.</p></article><article className="landing-feature-card"><span className="landing-feature-icon"><FileSearch size={22}/></span><h3>Documentation review</h3><p>Organize document findings and compare supporting information with the claims being assessed.</p></article><article className="landing-feature-card"><span className="landing-feature-icon"><BrainCircuit size={22}/></span><h3>AI-assisted workflow</h3><p>Coordinate the available analysis stages and keep results together for a clearer review.</p></article></div></section>
      <section className="landing-how" id="how-it-works"><div className="landing-section-heading"><span className="landing-eyebrow">HOW IT WORKS</span><h2>From submission to informed review.</h2></div><div className="landing-steps"><article><span className="landing-step-number">01</span><h3>Submit</h3><p>Provide a project and the information you want evaluated.</p></article><article><span className="landing-step-number">02</span><h3>Analyze</h3><p>Run the available verification stages and collect their findings.</p></article><article><span className="landing-step-number">03</span><h3>Review</h3><p>Inspect the returned evidence and assess the results.</p></article></div></section>
      <section className="landing-final-cta"><div><span className="landing-eyebrow">YOUR WORKSPACE STARTS HERE</span><h2>Make verification a more structured process.</h2><p>Create an account to access your VeriFyra AI workspace.</p></div><Link to="/register" className="landing-primary-button">Create your account <ArrowRight size={17}/></Link></section>
    </main><footer className="landing-footer"><Link to="/" className="landing-brand"><span className="landing-logo"><ShieldCheck size={21}/></span><span>VeriFyra<span className="brand-accent"> AI</span></span></Link><span>AI-assisted verification. Evidence-led decisions.</span><span>© {new Date().getFullYear()} VeriFyra AI</span></footer>
  </div>;
}
