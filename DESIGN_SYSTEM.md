# Design System - IBARECISA

> Sistema de design unificado para o Sistema de Administração da Igreja Batista Regular de Cidade Satélite

---

## 1. Identidade Visual

### 1.1 Cores

#### Cores Primárias
A paleta roxa/magenta mantida da identidade atual, refinada para melhor acessibilidade:

```css
/* Primária - Ação principal, destaques */
--primary-50: #f5f3ff;
--primary-100: #ede9fe;
--primary-200: #ddd6fe;
--primary-300: #c4b5fd;
--primary-400: #a78bfa;
--primary-500: #8b5cf6;  /* Cor principal */
--primary-600: #7c3aed;
--primary-700: #6d28d9;
--primary-800: #5b21b6;
--primary-900: #4c1d95;
```

#### Cores Secundárias
Gradiente complementar para destaques:

```css
/* Secundária - Acompanha a primária */
--secondary-50: #fdf4ff;
--secondary-100: #fae8ff;
--secondary-200: #f5d0fe;
--secondary-300: #f0abfc;
--secondary-400: #e879f9;
--secondary-500: #d946ef;  /* Cor secundária */
--secondary-600: #c026d3;
--secondary-700: #a21caf;
--secondary-800: #86198f;
--secondary-900: #701a75;
```

#### Cores Neutras
Para textos, fundos e bordas:

```css
/* Neutros - Textos, fundos, bordas */
--slate-50: #f8fafc;
--slate-100: #f1f5f9;
--slate-200: #e2e8f0;
--slate-300: #cbd5e1;
--slate-400: #94a3b8;
--slate-500: #64748b;
--slate-600: #475569;
--slate-700: #334155;
--slate-800: #1e293b;
--slate-900: #0f172a;
```

#### Cores Semânticas
Para feedback visual:

```css
/* Sucesso */
--success-50: #f0fdf4;
--success-500: #22c55e;
--success-600: #16a34a;
--success-700: #15803d;

/* Aviso */
--warning-50: #fffbeb;
--warning-500: #f59e0b;
--warning-600: #d97706;
--warning-700: #b45309;

/* Erro */
--error-50: #fef2f2;
--error-500: #ef4444;
--error-600: #dc2626;
--error-700: #b91c1c;

/* Informação */
--info-50: #eff6ff;
--info-500: #3b82f6;
--info-600: #2563eb;
--info-700: #1d4ed8;
```

### 1.2 Gradientes

```css
/* Gradiente Primário - Para headers e botões principais */
--gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%);

/* Gradiente Secundário - Para hover states */
--gradient-primary-hover: linear-gradient(135deg, #7c3aed 0%, #c026d3 100%);

/* Gradiente Sutil - Para cards e backgrounds */
--gradient-subtle: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
```

---

## 2. Tipografia

### 2.1 Fontes

```css
/* Fonte Primária - Inter (Google Fonts) */
font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;

/* Fonte Mono - Para código e dados técnicos */
font-family: 'JetBrains Mono', ui-monospace, monospace;
```

### 2.2 Escala Tipográfica

```css
/* Display */
text-display-2xl: 4.5rem;   /* 72px - Landing hero */
text-display-xl: 3.75rem;   /* 60px - Page titles */
text-display-lg: 3rem;      /* 48px - Section titles */

/* Headings */
text-h1: 2.25rem;           /* 36px - Main page heading */
text-h2: 1.875rem;          /* 30px - Section heading */
text-h3: 1.5rem;            /* 24px - Subsection heading */
text-h4: 1.25rem;           /* 20px - Card heading */
text-h5: 1.125rem;          /* 18px - Small heading */
text-h6: 1rem;              /* 16px - Smallest heading */

/* Body */
text-xl: 1.25rem;           /* 20px - Large body */
text-lg: 1.125rem;          /* 18px - Body large */
text-base: 1rem;            /* 16px - Body base */
text-sm: 0.875rem;          /* 14px - Body small */
text-xs: 0.75rem;           /* 12px - Caption */
```

### 2.3 Pesos de Fonte

```css
font-light: 300;
font-normal: 400;
font-medium: 500;
font-semibold: 600;
font-bold: 700;
```

### 2.4 Linha de Altura

```css
leading-tight: 1.25;
leading-normal: 1.5;
leading-relaxed: 1.625;
```

---

## 3. Espaçamentos

### 3.1 Escala de Espaçamento

```css
/* Base unit: 0.25rem (4px) */
spacing-0: 0;
spacing-1: 0.25rem;    /* 4px */
spacing-2: 0.5rem;     /* 8px */
spacing-3: 0.75rem;    /* 12px */
spacing-4: 1rem;       /* 16px */
spacing-5: 1.25rem;    /* 20px */
spacing-6: 1.5rem;     /* 24px */
spacing-8: 2rem;       /* 32px */
spacing-10: 2.5rem;    /* 40px */
spacing-12: 3rem;      /* 48px */
spacing-16: 4rem;      /* 64px */
spacing-20: 5rem;      /* 80px */
spacing-24: 6rem;      /* 96px */
```

### 3.2 Espaçamentos Semânticos

```css
/* Container padding */
container-padding: 1.5rem;        /* 24px */
container-padding-lg: 2rem;       /* 32px */

/* Section spacing */
section-spacing: 4rem;            /* 64px */

/* Card spacing */
card-padding: 1.5rem;             /* 24px */
card-padding-lg: 2rem;            /* 32px */

/* Form spacing */
form-gap: 1rem;                   /* 16px */
form-group-gap: 1.5rem;           /* 24px */
```

---

## 4. Bordas e Sombras

### 4.1 Raios de Borda

```css
radius-none: 0;
radius-sm: 0.25rem;      /* 4px - Small elements */
radius-base: 0.5rem;     /* 8px - Buttons, inputs */
radius-md: 0.75rem;      /* 12px - Cards */
radius-lg: 1rem;         /* 16px - Modals */
radius-xl: 1.5rem;       /* 24px - Hero sections */
radius-full: 9999px;     /* Circular elements */
```

### 4.2 Sombras

```css
/* Sombras de Elevação */
shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
shadow-base: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);

/* Sombras Coloridas */
shadow-primary: 0 4px 14px 0 rgb(139 92 246 / 0.25);
shadow-primary-lg: 0 8px 30px 0 rgb(139 92 246 / 0.3);

/* Sombras Internas */
shadow-inner: inset 0 2px 4px 0 rgb(0 0 0 / 0.05);
```

---

## 5. Componentes

### 5.1 Botões

#### Botão Primário
```css
.btn-primary {
  background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%);
  color: white;
  padding: 0.625rem 1.5rem;  /* 10px 24px */
  border-radius: 0.5rem;      /* 8px */
  font-weight: 500;
  transition: all 0.2s ease;
  box-shadow: 0 4px 14px 0 rgb(139 92 246 / 0.25);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #7c3aed 0%, #c026d3 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px 0 rgb(139 92 246 / 0.35);
}

.btn-primary:active {
  transform: translateY(0);
}
```

#### Botão Secundário
```css
.btn-secondary {
  background: white;
  color: #7c3aed;
  border: 1px solid #e2e8f0;
  padding: 0.625rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: #f8fafc;
  border-color: #c4b5fd;
  color: #6d28d9;
}
```

#### Botão de Perigo
```css
.btn-danger {
  background: #ef4444;
  color: white;
  padding: 0.625rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-danger:hover {
  background: #dc2626;
  transform: translateY(-1px);
}
```

#### Tamanhos de Botão
```css
.btn-sm {
  padding: 0.375rem 0.875rem;  /* 6px 14px */
  font-size: 0.875rem;          /* 14px */
}

.btn-lg {
  padding: 0.75rem 2rem;        /* 12px 32px */
  font-size: 1.125rem;          /* 18px */
}
```

### 5.2 Formulários

#### Input de Texto
```css
.input {
  width: 100%;
  padding: 0.75rem 1rem;        /* 12px 16px */
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;        /* 8px */
  font-size: 1rem;              /* 16px */
  background: white;
  transition: all 0.2s ease;
  color: #1e293b;
}

.input:hover {
  border-color: #c4b5fd;
}

.input:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgb(139 92 246 / 0.1);
}

.input:disabled {
  background: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

.input-error {
  border-color: #ef4444;
}

.input-error:focus {
  box-shadow: 0 0 0 3px rgb(239 68 68 / 0.1);
}
```

#### Label
```css
.label {
  display: block;
  font-size: 0.875rem;          /* 14px */
  font-weight: 500;
  color: #334155;
  margin-bottom: 0.375rem;      /* 6px */
}

.label-required::after {
  content: " *";
  color: #ef4444;
}
```

#### Mensagem de Erro
```css
.input-error-message {
  display: flex;
  align-items: center;
  gap: 0.375rem;                /* 6px */
  margin-top: 0.375rem;         /* 6px */
  font-size: 0.875rem;          /* 14px */
  color: #ef4444;
}
```

#### Select
```css
.select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3E%3C/svg%3E");
  background-position: right 0.75rem center;
  background-repeat: no-repeat;
  background-size: 1.25rem;
  padding-right: 2.5rem;
}
/* Usa os mesmos estilos do .input */
```

#### Textarea
```css
.textarea {
  min-height: 120px;
  resize: vertical;
}
/* Usa os mesmos estilos do .input */
```

#### Checkbox e Radio
```css
.checkbox, .radio {
  width: 1.125rem;              /* 18px */
  height: 1.125rem;             /* 18px */
  border: 1px solid #e2e8f0;
  border-radius: 0.25rem;       /* 4px */
  cursor: pointer;
  transition: all 0.2s ease;
}

.radio {
  border-radius: 9999px;
}

.checkbox:checked, .radio:checked {
  background: #8b5cf6;
  border-color: #8b5cf6;
}
```

### 5.3 Cards

#### Card Base
```css
.card {
  background: white;
  border-radius: 0.75rem;       /* 12px */
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
}

.card:hover {
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  transform: translateY(-2px);
}
```

#### Card Header
```css
.card-header {
  background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%);
  color: white;
  padding: 1.5rem;              /* 24px */
}

.card-header-secondary {
  background: #f8fafc;
  color: #1e293b;
  border-bottom: 1px solid #e2e8f0;
  padding: 1.25rem;             /* 20px */
}
```

#### Card Body
```css
.card-body {
  padding: 1.5rem;              /* 24px */
}

.card-body-lg {
  padding: 2rem;                /* 32px */
}
```

#### Card Footer
```css
.card-footer {
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  padding: 1rem 1.5rem;         /* 16px 24px */
  font-size: 0.875rem;          /* 14px */
  color: #64748b;
}
```

### 5.4 Tabelas

```css
.table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.table thead th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
  text-align: left;
  padding: 0.75rem 1rem;        /* 12px 16px */
  border-bottom: 2px solid #e2e8f0;
  font-size: 0.75rem;           /* 12px */
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.table tbody tr {
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.2s ease;
}

.table tbody tr:hover {
  background: #f8fafc;
}

.table tbody td {
  padding: 0.875rem 1rem;       /* 14px 16px */
  color: #334155;
}

.table tbody tr:last-child td {
  border-bottom: none;
}
```

### 5.5 Notificações (Toasts)

```css
.toast {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;                 /* 12px */
  padding: 1rem 1.25rem;        /* 16px 20px */
  border-radius: 0.5rem;        /* 8px */
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-success {
  background: #f0fdf4;
  border: 1px solid #86efac;
  color: #166534;
}

.toast-error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #991b1b;
}

.toast-warning {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  color: #92400e;
}

.toast-info {
  background: #eff6ff;
  border: 1px solid #93c5fd;
  color: #1e40af;
}
```

### 5.6 Navbar

```css
.navbar {
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
  padding: 0.75rem 1.5rem;      /* 12px 24px */
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}

.navbar-brand {
  font-weight: 700;
  font-size: 1.25rem;           /* 20px */
  color: white;
  text-decoration: none;
}

.nav-link {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  padding: 0.5rem 1rem;         /* 8px 16px */
  border-radius: 0.375rem;      /* 6px */
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.nav-link.active {
  color: white;
  background: rgba(255, 255, 255, 0.2);
}
```

### 5.7 Badges

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.625rem;    /* 4px 10px */
  font-size: 0.75rem;           /* 12px */
  font-weight: 600;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge-primary {
  background: #ede9fe;
  color: #6d28d9;
}

.badge-success {
  background: #dcfce7;
  color: #166534;
}

.badge-warning {
  background: #fef3c7;
  color: #92400e;
}

.badge-error {
  background: #fee2e2;
  color: #991b1b;
}
```

### 5.8 Modais

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  animation: fadeIn 0.2s ease;
}

.modal {
  background: white;
  border-radius: 1rem;          /* 16px */
  box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25);
  max-width: 32rem;             /* 512px */
  width: 90%;
  animation: modalSlide 0.3s ease;
}

@keyframes modalSlide {
  from {
    transform: scale(0.95) translateY(10px);
    opacity: 0;
  }
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

.modal-header {
  padding: 1.5rem;              /* 24px */
  border-bottom: 1px solid #e2e8f0;
}

.modal-body {
  padding: 1.5rem;              /* 24px */
}

.modal-footer {
  padding: 1rem 1.5rem;         /* 16px 24px */
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 0.75rem;                 /* 12px */
  justify-content: flex-end;
}
```

---

## 6. Layouts

### 6.1 Container

```css
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1.5rem;            /* 24px */
}

.container-sm {
  max-width: 640px;
}

.container-md {
  max-width: 768px;
}

.container-lg {
  max-width: 1024px;
}

.container-xl {
  max-width: 1280px;
}
```

### 6.2 Grid

```css
.grid {
  display: grid;
  gap: 1.5rem;                  /* 24px */
}

.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }

@media (max-width: 768px) {
  .grid-cols-2,
  .grid-cols-3,
  .grid-cols-4 {
    grid-template-columns: 1fr;
  }
}
```

---

## 7. Estados

### 7.1 Hover
```css
/* Botões e elementos interativos */
hover-lift: translateY(-2px);
hover-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
```

### 7.2 Focus
```css
/* Acessibilidade */
focus-ring: 0 0 0 3px rgb(139 92 246 / 0.1);
focus-outline: 2px solid #8b5cf6;
focus-offset: outline-offset 2px;
```

### 7.3 Disabled
```css
disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
```

### 7.4 Loading
```css
loading {
  position: relative;
  color: transparent;
}

loading::after {
  content: "";
  position: absolute;
  width: 1rem;
  height: 1rem;
  top: 50%;
  left: 50%;
  margin-left: -0.5rem;
  margin-top: -0.5rem;
  border: 2px solid #e2e8f0;
  border-top-color: #8b5cf6;
  border-radius: 9999px;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

---

## 8. Backgrounds

### 8.1 Backgrounds Semânticos

```css
bg-primary: #8b5cf6;
bg-secondary: #f8fafc;
bg-accent: #faf5ff;

bg-success: #f0fdf4;
bg-warning: #fffbeb;
bg-error: #fef2f2;
bg-info: #eff6ff;
```

### 8.2 Backgrounds de Seção

```css
bg-hero: linear-gradient(135deg, #f5f3ff 0%, #fae8ff 100%);
bg-light: #f8fafc;
bg-white: #ffffff;
```

---

## 9. Animações

### 9.1 Transições

```css
transition-fast: 150ms ease;
transition-base: 200ms ease;
transition-slow: 300ms ease;
```

### 9.2 Keyframes

```css
/* Fade */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide */
@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Scale */
@keyframes scaleIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
```

---

## 10. Responsividade

### 10.1 Breakpoints

```css
sm: 640px;   /* Small devices */
md: 768px;   /* Medium devices */
lg: 1024px;  /* Large devices */
xl: 1280px;  /* Extra large devices */
2xl: 1536px; /* 2X large devices */
```

### 10.2 Media Queries

```css
/* Mobile First Approach */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
```

---

## 11. Acessibilidade

### 11.1 Contraste
- Texto sobre fundo claro: mínimo 4.5:1 (WCAG AA)
- Texto grande sobre fundo claro: mínimo 3:1 (WCAG AA)
- Texto sobre fundo escuro: mínimo 7:1 (WCAG AAA)

### 11.2 Focus
- Todos os elementos interativos devem ter estado de focus visível
- Usar `focus-ring` ou `focus-outline` em todos os botões e inputs

### 11.3 Tamanho de Toque Mínimo
- Botões e links: mínimo 44x44 pixels

---

## 12. Implementação Tailwind v4

Adicionar ao `input.css`:

```css
@import "tailwindcss";

@source "../../*.html";
@source "../../templates/**/*.html";
@source "../../../blog/templates/**/*.html";

/* Cores personalizadas */
@theme {
  --color-primary-50: #f5f3ff;
  --color-primary-100: #ede9fe;
  --color-primary-200: #ddd6fe;
  --color-primary-300: #c4b5fd;
  --color-primary-400: #a78bfa;
  --color-primary-500: #8b5cf6;
  --color-primary-600: #7c3aed;
  --color-primary-700: #6d28d9;
  --color-primary-800: #5b21b6;
  --color-primary-900: #4c1d95;

  --color-secondary-500: #d946ef;
  --color-secondary-600: #c026d3;

  --gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%);

  --radius-base: 0.5rem;
  --radius-md: 0.75rem;

  --shadow-primary: 0 4px 14px 0 rgb(139 92 246 / 0.25);
}

/* Fontes */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
```

---

## 13. Exemplos de Uso

### 13.1 Formulário de Login
```html
<div class="max-w-md mx-auto">
  <div class="bg-white rounded-xl shadow-md overflow-hidden">
    <div class="bg-gradient-to-r from-primary-500 to-secondary-500 p-6">
      <h2 class="text-2xl font-bold text-white">Entrar</h2>
    </div>
    <form class="p-6 space-y-4">
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Email</label>
        <input type="email" class="w-full px-4 py-3 rounded-lg border border-slate-200 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 outline-none transition">
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Senha</label>
        <input type="password" class="w-full px-4 py-3 rounded-lg border border-slate-200 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 outline-none transition">
      </div>
      <button type="submit" class="w-full py-3 bg-gradient-to-r from-primary-500 to-secondary-500 text-white font-medium rounded-lg shadow-primary hover:-translate-y-0.5 hover:shadow-lg transition-all">
        Entrar
      </button>
    </form>
  </div>
</div>
```

### 13.2 Card de Postagem
```html
<div class="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg hover:-translate-y-0.5 transition-all">
  <div class="bg-gradient-to-r from-primary-500 to-secondary-500 p-6">
    <h3 class="text-xl font-semibold text-white">Título da Postagem</h3>
  </div>
  <div class="p-6">
    <p class="text-slate-600 leading-relaxed">Conteúdo da postagem...</p>
  </div>
  <div class="bg-slate-50 px-6 py-4 border-t border-slate-100 flex justify-between items-center">
    <span class="text-sm text-slate-500">Por João Silva em 29/01/2026</span>
    <span class="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-semibold uppercase tracking-wide">Categoria</span>
  </div>
</div>
```

---

**Versão:** 1.0
**Data:** 29 de Janeiro de 2026
**Framework:** Tailwind CSS v4
**Aplicação:** IBARECISA - Sistema de Administração da Igreja Batista Regular de Cidade Satélite
