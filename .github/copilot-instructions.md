# PetCloud Project - AI Agent Instructions

## Project Overview
PetCloud is a frontend-focused web application for pet management and community engagement. The project uses semantic HTML5 and responsive CSS3, following a multi-page architecture without a backend framework.

## Key Architecture Patterns

### Page Structure
All HTML pages are located in the `pages/` directory:
- Entry point: `pages/index.html` (landing page)
- Authentication flow: `pages/cadastro.html` (registration) → `pages/login.html` → `pages/recuperar-senha.html` (password recovery)
- Main application flow: `pages/dashboard.html` → `pages/listagem.html` (pet list) → `pages/detalhes.html`/`pages/detalhes-mimi.html` (pet details)
- Community features: `pages/concurso.html` (pet contests and voting)

### Design Patterns
- CSS follows a global-first approach in `css/style.css`
- Common components (e.g., navigation bars) use consistent class naming:
  - `.top-bar` for navigation headers
  - `.hero-section` for main content areas
  - Global styles use system font stack for consistent typography

### Responsive Design
- Mobile-first approach with flexbox layouts
- Breakpoints handle tablet and desktop views
- Video backgrounds adapt to screen sizes (see `hero-video-container` class)

### Asset Organization
```
PetCloud/
├── pages/             # HTML templates
│   ├── index.html
│   ├── cadastro.html
│   └── ...
├── css/              # Stylesheets
│   └── style.css
├── imagens/          # Image assets
└── video/            # Video assets
```

## Development Workflow
1. New pages should be created in the `pages/` directory
2. Use relative paths (`../`) to reference assets from page templates
3. Use the existing font stack and color scheme from `style.css`
4. Maintain responsive design patterns across all new components

## Common Patterns to Follow
- Use semantic HTML5 elements (`<nav>`, `<main>`, `<section>`)
- Include proper language attributes (`lang="pt-BR"`)
- Maintain accessibility with proper ARIA attributes
- Follow the existing color scheme: primary background `#c4e9f7`, text color `#1a1a1a`

## Testing
- Test all pages across desktop, tablet, and mobile viewports
- Verify video playback works with fallback message
- Check responsive behavior of all interactive elements
- Test relative paths work correctly from all pages

## Notes
- Project uses plain HTML/CSS without build tools or preprocessors
- All media queries and animations are in `style.css`
- Pages follow a consistent structure with top navigation bar