import React, { useState } from 'react';
import './index.css';

// ─── Config por Plano ──────────────────────────────────────────────
const PLAN_CONFIG = {
  alpha: {
    name: 'Alpha',
    generations: 10,
    headline: 'Visualize a Porta Perfeita',
    headlineHighlight: 'no Seu Ambiente',
    description: 'Envie a foto do seu espaço e do modelo de porta. Nossa IA gera uma simulação realista em segundos — grátis.',
    ctaText: 'Começar Grátis',
    ctaLink: 'https://t.me/simuladoralfabot?start=alpha',
    ctaIcon: '🚀',
    secondaryText: 'Ver como funciona',
    badgeText: 'Gratuito • 10 simulações',
    formTitle: 'Acesse o Simulador Grátis',
    formDescription: 'Preencha seus dados para ser redirecionado ao nosso assistente no Telegram.',
    platform: 'Telegram',
  },
  beta: {
    name: 'Beta',
    generations: 20,
    headline: 'Simulador de Portas',
    headlineHighlight: 'com IA de Alta Fidelidade',
    description: 'Receba 20 simulações com maior qualidade e velocidade. Converse diretamente pelo WhatsApp com nossa IA.',
    ctaText: 'Acessar pelo WhatsApp',
    // TODO: Substituir pelo número real do WhatsApp Business
    ctaLink: 'https://wa.me/SEU_NUMERO_AQUI?text=Quero%20acessar%20o%20Simulador%20Beta',
    ctaIcon: '💬',
    secondaryText: 'Saiba mais',
    badgeText: 'Acesso Gratuito • 20 simulações',
    formTitle: 'Receba Acesso ao Plano Beta',
    formDescription: 'Preencha seus dados e comece a simular pelo WhatsApp agora.',
    platform: 'WhatsApp',
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
    badgeText: 'Profissional • 200 simulações',
    formTitle: 'Assinar o Plano Omega',
    formDescription: 'Complete seus dados para ser redirecionado ao checkout seguro.',
    platform: 'WhatsApp',
  },
};

// Definir qual plano esta LP mostra (pode ler da URL futuramente)
const CURRENT_PLAN = 'alpha';
const config = PLAN_CONFIG[CURRENT_PLAN];

// ─── Componentes ───────────────────────────────────────────────────

function Navbar() {
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

function Hero() {
  return (
    <section className="hero" id="hero">
      <div className="hero-inner">
        <div className="hero-text">
          <div className="hero-badge animate-in delay-1">
            <span className="dot"></span>
            {config.badgeText}
          </div>

          <h1 className="animate-in delay-2">
            {config.headline}
            <br />
            <span className="highlight">{config.headlineHighlight}</span>
          </h1>

          <p className="hero-description animate-in delay-3">
            {config.description}
          </p>

          <div className="hero-buttons animate-in delay-4">
            <a href="#form">
              <button className="btn-primary">
                {config.ctaIcon} {config.ctaText}
              </button>
            </a>
            <a href="#form">
              <button className="btn-secondary">
                {config.secondaryText} →
              </button>
            </a>
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

function FormSection() {
  const [formData, setFormData] = useState({ nome: '', telefone: '', email: '' });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Redirecionar conforme o plano
    if (CURRENT_PLAN === 'omega') {
      // Omega: redirecionar para checkout
      window.location.href = 'https://kiwify.com.br/checkout/omega';
    } else if (CURRENT_PLAN === 'beta') {
      // Beta: redirecionar para WhatsApp
      window.location.href = config.ctaLink;
    } else {
      // Alpha: redirecionar para Telegram
      window.location.href = config.ctaLink;
    }
    setSubmitted(true);
  };

  return (
    <section className="form-section" id="form">
      <div className="form-container animate-in">
        <h2>{config.formTitle}</h2>
        <p>{config.formDescription}</p>

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
            <button type="submit" className="form-submit">
              {config.ctaIcon} {config.ctaText}
            </button>
            <p className="form-disclaimer">
              Ao continuar, você concorda com nossa Política de Privacidade.
            </p>
          </form>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <p style={{ fontSize: '2rem', marginBottom: '12px' }}>✅</p>
            <p style={{ fontWeight: 600 }}>Redirecionando...</p>
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
        <p className="footer-text">
          © 2026 Simulador de Portas IA. Todos os direitos reservados.
        </p>
        <div className="footer-links">
          <a href="#">Termos de Uso</a>
          <a href="#">Privacidade</a>
          <a href="#">Suporte</a>
        </div>
      </div>
    </footer>
  );
}

// ─── App Principal ─────────────────────────────────────────────────

function App() {
  return (
    <>
      <Navbar />
      <Hero />
      <FormSection />
      <Footer />
    </>
  );
}

export default App;
