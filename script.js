/* ==========================================
   OUT THE TRUNK - INTERACTIVE NAVIGATION
   ========================================== */

function initMobileMenu() {
  var navToggle = document.querySelector('.nav-toggle');
  var siteNav = document.getElementById('site-nav') || document.querySelector('.site-header nav');

  if (navToggle && siteNav) {
    // Clear inline styles if present
    siteNav.removeAttribute('style');

    navToggle.addEventListener('click', function(e) {
      e.stopPropagation();
      var isOpen = siteNav.classList.contains('is-open');
      
      if (isOpen) {
        siteNav.classList.remove('is-open');
        navToggle.setAttribute('aria-expanded', 'false');
      } else {
        siteNav.classList.add('is-open');
        navToggle.setAttribute('aria-expanded', 'true');
      }
    });

    // Close menu when clicking anywhere outside header nav
    document.addEventListener('click', function(e) {
      if (!siteNav.contains(e.target) && !navToggle.contains(e.target)) {
        siteNav.classList.remove('is-open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });

    // Close menu when a navigation link is clicked
    var navLinks = siteNav.querySelectorAll('a');
    for (var i = 0; i < navLinks.length; i++) {
      navLinks[i].addEventListener('click', function() {
        siteNav.classList.remove('is-open');
        navToggle.setAttribute('aria-expanded', 'false');
      });
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMobileMenu);
} else {
  initMobileMenu();
}