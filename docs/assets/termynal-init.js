/**
 * Initialise all [data-termynal] containers on page load.
 * Uses a data attribute to prevent double-initialisation on the same element.
 */
function initTermynals() {
    document.querySelectorAll('[data-termynal]:not([data-termynal-loaded])').forEach(function (node) {
        node.setAttribute('data-termynal-loaded', '');
        new Termynal(node, { lineDelay: 700, typeDelay: 40 });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTermynals);
} else {
    initTermynals();
}
