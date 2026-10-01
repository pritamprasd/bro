// =========================================================================
// BRO THEME ENGINE
// =========================================================================

    function setSystemTheme(themeName) {
      if (themeName !== 'default' && themeName !== 'neumorphism' && themeName !== 'glassmorphism') {
        themeName = 'default';
      }
      document.documentElement.setAttribute('data-theme', themeName);
      localStorage.setItem('bro_system_theme', themeName);

      // Update card active classes
      document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
      const activeCard = document.getElementById('theme-card-' + themeName);
      if (activeCard) activeCard.classList.add('active');

      const dotDef = document.getElementById('dot-theme-default');
      const dotNeu = document.getElementById('dot-theme-neumorphism');
      const dotGlass = document.getElementById('dot-theme-glassmorphism');
      if (dotDef && dotNeu) {
        dotDef.className = (themeName === 'default') ? 'status-dot dot-green' : 'status-dot dot-gray';
        dotNeu.className = (themeName === 'neumorphism') ? 'status-dot dot-green' : 'status-dot dot-gray';
        if (dotGlass) dotGlass.className = (themeName === 'glassmorphism') ? 'status-dot dot-green' : 'status-dot dot-gray';
      }

      const badge = document.getElementById('theme-active-badge');
      if (badge) {
        if (themeName === 'glassmorphism') {
          badge.innerText = 'AURORA GLASSMORPHISM';
          badge.style.color = '#00e5ff';
          badge.style.borderColor = '#00e5ff';
        } else if (themeName === 'neumorphism') {
          badge.innerText = 'NEOMORPHISM ACTIVE';
          badge.style.color = '#00d2ff';
          badge.style.borderColor = '#00d2ff';
        } else {
          badge.innerText = 'DEFAULT CYBER';
          badge.style.color = '#a855f7';
          badge.style.borderColor = '#a855f7';
        }
      }

      playTacticalSfx('click');
      appendLog('step', `🎨 System UX Theme switched to: ${themeName.toUpperCase()}`);
    }


    function initThemeUI() {
      const currentTheme = localStorage.getItem('bro_system_theme') || 'default';
      document.documentElement.setAttribute('data-theme', currentTheme);

      document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
      const activeCard = document.getElementById('theme-card-' + currentTheme);
      if (activeCard) activeCard.classList.add('active');

      const dotDef = document.getElementById('dot-theme-default');
      const dotNeu = document.getElementById('dot-theme-neumorphism');
      const dotGlass = document.getElementById('dot-theme-glassmorphism');
      if (dotDef && dotNeu) {
        dotDef.className = (currentTheme === 'default') ? 'status-dot dot-green' : 'status-dot dot-gray';
        dotNeu.className = (currentTheme === 'neumorphism') ? 'status-dot dot-green' : 'status-dot dot-gray';
        if (dotGlass) dotGlass.className = (currentTheme === 'glassmorphism') ? 'status-dot dot-green' : 'status-dot dot-gray';
      }

      const badge = document.getElementById('theme-active-badge');
      if (badge) {
        if (currentTheme === 'glassmorphism') {
          badge.innerText = 'AURORA GLASSMORPHISM';
          badge.style.color = '#00e5ff';
          badge.style.borderColor = '#00e5ff';
        } else if (currentTheme === 'neumorphism') {
          badge.innerText = 'NEOMORPHISM ACTIVE';
          badge.style.color = '#00d2ff';
          badge.style.borderColor = '#00d2ff';
        } else {
          badge.innerText = 'DEFAULT CYBER';
          badge.style.color = '#a855f7';
          badge.style.borderColor = '#a855f7';
        }
      }
    }
