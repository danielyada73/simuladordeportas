import React, { useState, useMemo } from 'react';
import './index.css';

// ─── Config por Plano ──────────────────────────────────────────────
const PLAN_CONFIG = {
  alpha: {
    name: 'Alpha',
    generations: 10,
    headline: 'Visualize a Porta Perfeita',
    headlineHighlight: 'no Seu Ambiente',
    description: 'Envie a foto do seu espaço e do modelo de porta. Nossa IA gera uma simulação realista em segundos — grátis.',
    ctaText: 'Começar Grátis no Telegram',
    ctaLink: 'https://t.me/simuladoralfabot?start=alpha',
    ctaIcon: '🚀',
    secondaryText: 'Ver como funciona',
    badgeText: '✦ Gratuito • 10 simulações',
    formTitle: 'Acesse o Simulador Grátis',
    formDescription: 'Preencha seus dados e seja redirecionado ao nosso assistente no Telegram.',
    platform: 'Telegram',
    platformIcon: '✈️',
    accentColor: '#7c5cfc',
    showForm: true,
  },
  beta: {
    name: 'Beta',
    generations: 20,
    headline: 'Simulações de Alta Fidelidade',
    headlineHighlight: 'Direto no Seu WhatsApp',
    description: '20 simulações com IA avançada. Envie suas fotos pelo WhatsApp e receba o resultado na hora.',
    ctaText: 'Acessar pelo WhatsApp',
    ctaLink: 'https://wa.me/15556303616?text=Ol%C3%A1!%20Quero%20acessar%20o%20Simulador%20Beta',
    ctaIcon: '💬',
    secondaryText: 'Saiba mais',
    badgeText: '✦ Acesso Gratuito • 20 simulações',
    formTitle: 'Receba Acesso ao Plano Beta',
    formDescription: 'Preencha seus dados e comece a simular pelo WhatsApp.',
    platform: 'WhatsApp',
    platformIcon: '📱',
    accentColor: '#25D366',
    showForm: true,
  },
  omega: {
    name: 'Omega',
    generations: 200,
    headline: 'O Plano Profissional',
    headlineHighlight: 'para Quem é Profissional',
    description: '200 simulações em alta fidelidade com suporte prioritário. Ideal para lojas, arquitetos e decoradores.',
    ctaText: 'Assinar Plano Omega',
    ctaLink: '#form',
    ctaIcon: '👑',
    secondaryText: 'Ver preço',
    badgeText: '✦ Profissional • 200 simulações',
    formTitle: 'Assine o Plano Omega',
    formDescription: 'Complete seus dados para ser redirecionado ao checkout seguro.',
    platform: 'WhatsApp',
    platformIcon: '👑',
    accentColor: '#f59e0b',
    showForm: true,
    // TODO: Substituir pela URL real do checkout (Kiwify, Mercado Pago, etc.)
    checkoutUrl: 'https://wa.me/15556303616?text=Quero%20assinar%20o%20Plano%20Omega',
  },
};

// ─── Detectar plano pela URL ────────────────────────────────────────
function getPlanFromURL() {
  const params = new URLSearchParams(window.location.search);
  const plan = params.get('plan')?.toLowerCase();
  if (plan && PLAN_CONFIG[plan]) return plan;

  // Fallback: detectar pelo pathname (/alpha, /beta, /omega)
  const path = window.location.pathname.replace('/', '').toLowerCase();
  if (path && PLAN_CONFIG[path]) return path;

  return 'alpha'; // padrão
}

// ─── Componentes ───────────────────────────────────────────────────

function Navbar({ config }) {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-logo">
          <div className="logo-icon">🚪</div>
          <span>Simulador de Portas</span>
        </div>
        <div className="navbar-links">
          <a href="#hero">Início</a>
          <a href="#form">Cadastro</a>
          <a href="#footer">Contato</a>
        </div>
        <a href="#form">
          <button className="navbar-cta">Começar Agora</button>
        </a>
      </div>
    </nav>
  );
}

function Hero({ config }) {
  return (
    <section className="hero" id="hero">
      <div className="hero-inner">
        <div className="hero-text">
          <div className="hero-badge animate-in delay-1">
            <span className="dot" style={{ background: config.accentColor }}></span>
            {config.badgeText}
          </div>

          <h1 className="animate-in delay-2">
            {config.headline}
            <br />
            <span className="highlight" style={{ '--accent': config.accentColor }}>
              {config.headlineHighlight}
            </span>
          </h1>

          <p className="hero-description animate-in delay-3">
            {config.description}
          </p>

          <div className="hero-buttons animate-in delay-4">
            <a href="#form">
              <button className="btn-primary" style={{ '--accent': config.accentColor }}>
                {config.ctaIcon} {config.ctaText}
              </button>
            </a>
            <a href="#form">
              <button className="btn-secondary">
                {config.secondaryText} →
              </button>
            </a>
          </div>

          <div className="hero-trust animate-in delay-5">
            <div className="trust-avatars">
              <div className="avatar">👩</div>
              <div className="avatar">👨</div>
              <div className="avatar">👩‍🦰</div>
              <div className="avatar">🧔</div>
            </div>
            <span>+500 simulações realizadas</span>
          </div>
        </div>

        <div className="hero-visual animate-in delay-3">
          <div className="hero-image-wrapper">
            <img src="/hero.png" alt="Simulação de porta com IA - antes e depois" />
            <span className="image-label left">Antes</span>
            <span className="image-label right">Depois</span>
          </div>

          <div className="float-card top-right">
            ✨ Gerado com IA
          </div>
          <div className="float-card bottom-left">
            ⚡ Resultado em segundos
          </div>
        </div>
      </div>
    </section>
  );
}

function FormSection({ config, planKey }) {
  const [formData, setFormData] = useState({ nome: '', telefone: '', email: '' });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);

    // Pequeno delay para mostrar "Redirecionando..." antes de sair
    setTimeout(() => {
      if (planKey === 'omega' && config.checkoutUrl) {
        window.location.href = config.checkoutUrl;
      } else {
        window.location.href = config.ctaLink;
      }
    }, 800);
  };

  return (
    <section className="form-section" id="form">
      <div className="form-container animate-in">
        <div className="form-header">
          <span className="form-plan-badge" style={{ background: config.accentColor }}>
            Plano {config.name}
          </span>
          <h2>{config.formTitle}</h2>
          <p>{config.formDescription}</p>
        </div>

        {!submitted ? (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="nome">Seu nome</label>
              <input
                id="nome"
                type="text"
                placeholder="Como podemos te chamar?"
                required
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label htmlFor="telefone">WhatsApp</label>
              <input
                id="telefone"
                type="tel"
                placeholder="(11) 99999-9999"
                required
                value={formData.telefone}
                onChange={(e) => setFormData({ ...formData, telefone: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label htmlFor="email">E-mail</label>
              <input
                id="email"
                type="email"
                placeholder="seu@email.com"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <button type="submit" className="form-submit" style={{ '--accent': config.accentColor }}>
              {config.ctaIcon} {config.ctaText}
            </button>
            <p className="form-disclaimer">
              🔒 Seus dados estão seguros. Ao continuar, você concorda com nossa Política de Privacidade.
            </p>
          </form>
        ) : (
          <div className="form-success">
            <div className="success-icon">✅</div>
            <p className="success-title">Cadastro realizado!</p>
            <p className="success-text">
              Redirecionando para o {config.platform}...
            </p>
            <div className="success-loader"></div>
          </div>
        )}
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer" id="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <div className="footer-logo">
            <span className="logo-icon">🚪</span>
            <span>Simulador de Portas IA</span>
          </div>
          <p className="footer-tagline">
            Visualize a porta perfeita no seu ambiente com inteligência artificial.
          </p>
        </div>
        <div className="footer-bottom">
          <p className="footer-text">
            © 2026 Simulador de Portas IA. Todos os direitos reservados.
          </p>
          <div className="footer-links">
            <a href="#">Termos de Uso</a>
            <a href="#">Privacidade</a>
            <a href="#">Suporte</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

// ─── App Principal ─────────────────────────────────────────────────

function App() {
  const planKey = useMemo(() => getPlanFromURL(), []);
  const config = PLAN_CONFIG[planKey];

  return (
    <>
      <Navbar config={config} />
      <Hero config={config} />
      <FormSection config={config} planKey={planKey} />
      <Footer />
    </>
  );
}

export default App;
