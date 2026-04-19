
/*
 * Polyfill pour atob() compatible IE9
 * Décodage Base64 standard
 */
if (typeof window.atob !== 'function') {
    window.atob = function (str) {
        var base64chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
        // Supprime tous les caractères qui ne sont pas Base64 valides
        str = String(str).replace(/[=]+$/, ''); // Supprime le padding '='
        str = str.replace(/[^A-Za-z0-9\+\/]/g, '');

        var output = '';
        var i = 0;
        var len = str.length;
        var chr1, chr2, chr3;
        var enc1, enc2, enc3, enc4;

        while (i < len) {
            enc1 = base64chars.indexOf(str.charAt(i++));
            enc2 = base64chars.indexOf(str.charAt(i++));
            enc3 = base64chars.indexOf(str.charAt(i++));
            enc4 = base64chars.indexOf(str.charAt(i++));

            chr1 = (enc1 << 2) | (enc2 >> 4);
            chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
            chr3 = ((enc3 & 3) << 6) | enc4;

            output = output + String.fromCharCode(chr1);

            if (enc3 !== 64) { // 64 = padding '='
                output = output + String.fromCharCode(chr2);
            }
            if (enc4 !== 64) {
                output = output + String.fromCharCode(chr3);
            }
        }
        return output;
    };
}

// --------------------------
// SlideToggle (vanilla jQuery-like) compatible IE9
// --------------------------
function slideToggle(el, duration) {
    if (!el) return;
    duration = duration || 300;
    var isHidden = getComputedStyle(el).display === "none";
    el.style.overflow = "hidden";
    el.style.transition = "height " + duration + "ms ease";

    if (isHidden) {
        el.style.display = "block";
        var h = el.scrollHeight;
        el.style.height = "0px";
        setTimeout(function () { el.style.height = h + "px"; }, 0);
        setTimeout(function () { el.style.height = ""; }, duration);
    } else {
        var h = el.offsetHeight;
        el.style.height = h + "px";
        setTimeout(function () { el.style.height = "0px"; }, 0);
        setTimeout(function () {
            el.style.display = "none";
            el.style.height = "";
        }, duration);
    }
}

function toggleHamburger(btn) {
    toggleClass(document.body, "site-menubar-open");
    toggleClass(btn, "hamburger-close");
    toggleClass(btn, "hided");
    toggleClass(btn, "unfolded");
}

function toggleMenu(link) {
    var submenu = link.nextElementSibling;
    var arrow = link.querySelector(".site-menu-arrow");
    slideToggle(submenu, 250);
    if (arrow) toggleClass(arrow, "tourne");
}

// --------------------------
// Modals (Bootstrap-like)
// --------------------------
function openModal(id) {
    var el = document.getElementById(id);
    if (!el) return;

    el.style.display = "block";
    void el.offsetWidth; // force reflow
    addClass(el, "in");

    addClass(document.body, "modal-open");

    if (!document.querySelector('.modal-backdrop')) {
        var backdrop = document.createElement('div');
        backdrop.className = "modal-backdrop";
        document.querySelector('.page').appendChild(backdrop);

        // Close modal if backdrop is clicked
        backdrop.onclick = function () { closeModal(); };

        setTimeout(function () { addClass(backdrop, "in"); }, 0);
    }
}

function closeModal() {
    var el = document.querySelector('.modal.in');
    if (!el) return;

    removeClass(el, "in");

    var backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) removeClass(backdrop, "in");

    var video = document.querySelector('#video');
    if (video) video.src = "";

    setTimeout(function () {
        el.style.display = "none";
        removeClass(document.body, "modal-open");
        if (backdrop && backdrop.parentNode) backdrop.parentNode.removeChild(backdrop);
    }, 250);
}

// --------------------------
// closest fallback IE9
// --------------------------
function closest(el, selector) {
    while (el && el.nodeType === 1) {
        if (elMatches(el, selector)) return el;
        el = el.parentNode;
    }
    return null;
}

function elMatches(el, selector) {
    var p = el.parentNode;
    if (!p) return false;
    var matches = p.querySelectorAll(selector) || [];
    for (var i = 0; i < matches.length; i++) {
        if (matches[i] === el) return true;
    }
    return false;
}

// --------------------------
// Activate / Cycle buttons
// --------------------------
function activerItem(id) {
    var btn = document.getElementById(id);
    if (!btn) return;

    var current = localStorage.getItem(id) || "btn-default";
    if (current === "btn-default") {
        replaceClass(btn, "btn-default", "btn-success");
        localStorage.setItem(id, "btn-success");
    }
}

function scs(btn) {
    if (typeof Storage === "undefined") return;
    var classes = ["btn-default", "btn-success", "btn-warning", "btn-danger"];
    var id = btn.id;

    var current = "btn-default";
    for (var i = 0; i < classes.length; i++) {
        if (btn.className.indexOf(classes[i]) !== -1) {
            current = classes[i];
            break;
        }
    }

    var next = classes[(classes.indexOf(current) + 1) % classes.length];
    replaceClass(btn, current, next);
    localStorage.setItem(id, next);
}

function searchItems(input) {
    var searchTerm = input.value.toLowerCase();
    var panel = input.parentNode.parentNode;
    if (!panel) return;

    var items = panel.querySelectorAll('.item');
    var count = 0;

    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        var a = item.querySelector('a');
        var text = a ? a.textContent.toLowerCase() : '';

        if (text.indexOf(searchTerm) !== -1) {
            item.style.display = 'inline-flex'; // OK
            count++;
        } else {
            item.style.display = 'none';
        }
    }

    var countElement = panel.querySelector('.items-count');
    if (countElement) countElement.textContent = count;
}

function searchSujetsSolutionFilter() {
    var checkbox = document.getElementById('filterSolution');
    checkbox.checked = !checkbox.checked;
    searchSujets();
}

function searchSujets() {
    var filterSearch = (document.getElementById('filterSearch').value || '').toLowerCase().trim();
    var filterSolution = document.getElementById('filterSolution').checked;

    var items = document.querySelectorAll('.item');
    var badge = document.querySelector('.items-sol');
    var visible = 0;

    // Toggle badge color
    if (filterSolution) {
        addClass(badge, 'bg-red-800');
        removeClass(badge, 'bg-3');
    } else {
        removeClass(badge, 'bg-red-800');
        addClass(badge, 'bg-3');
    }

    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        var text = (item.textContent || item.innerText || '').toLowerCase();
        var sol  = item.getAttribute('data-solution') === '1';

        var show = true;

        // Search filter
        if (filterSearch && text.indexOf(filterSearch) === -1) {
            show = false;
        }

        // Solution filter
        if (filterSolution && !sol) {
            show = false;
        }

        item.style.display = show ? '' : 'none';
        item.setAttribute('aria-hidden', show ? 'false' : 'true');

        if (show) visible++;
    }

    var counter = document.querySelector('.items-count');
    if (counter) {
        counter.textContent = visible;
    }
}

function colorer(c) {
    var colors = ["blue", "green", "purple", "pink"];
    var found = false;
    for (var i = 0; i < colors.length; i++) {
        removeClass(document.body, colors[i]);
        if (colors[i] === c) found = true;
    }
    if (!found) return;

    addClass(document.body, c);
    localStorage.setItem("color", c);
}

// --------------------------
// Helper functions
// --------------------------
function enc(str) {
    try { str = atob(str); } catch(e) { return '#'; }
    var result = '';
    for (var i = 0; i < str.length; i++) {
        result += String.fromCharCode(str.charCodeAt(i) - 8);
    }
    return result;
}

function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function timeAgo(timestamp, isArabic) {
    isArabic = !!isArabic;
    var seconds = Math.floor(Date.now() / 1000 - timestamp);
    var interval;
    if (seconds < 60) return isArabic ? 'الآن' : 'À l’instant';
    else if ((interval = Math.floor(seconds / 60)) < 60) return isArabic ? 'منذ ' + interval + ' دقيقة' : 'il y a ' + interval + ' minute' + (interval > 1 ? 's' : '');
    else if ((interval = Math.floor(seconds / 3600)) < 24) return isArabic ? 'منذ ' + interval + ' ساعة' : 'il y a ' + interval + ' heure' + (interval > 1 ? 's' : '');
    else if ((interval = Math.floor(seconds / 86400)) < 7) return isArabic ? 'منذ ' + interval + ' يوم' : 'il y a ' + interval + ' jour' + (interval > 1 ? 's' : '');
    else if ((interval = Math.floor(seconds / 604800)) < 4) return isArabic ? 'منذ ' + interval + ' أسبوع' : 'il y a ' + interval + ' semaine' + (interval > 1 ? 's' : '');
    else if ((interval = Math.floor(seconds / 2592000)) < 12) return isArabic ? 'منذ ' + interval + ' شهر' : 'il y a ' + interval + ' mois';
    else {
        var years = Math.floor(interval / 12);
        return isArabic ? 'منذ ' + years + ' سنة' : 'il y a ' + years + ' an' + (years > 1 ? 's' : '');
    }
}

function loadContent(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) callback(xhr.responseText);
            else callback('');
        }
    };
    xhr.send();
}

function setupBtn(selector, action) {
    var btns = document.querySelectorAll(selector);
    for (var i = 0; i < btns.length; i++) {
        (function (btn) {
            btn.onclick = function (e) {
                e = e || window.event;
                if (e && e.preventDefault) e.preventDefault(); else if (e) e.returnValue = false;
                action(btn);
            };
        })(btns[i]);
    }
}

function replaceClass(el, oldC, newC) {
    if (!el) return;
    removeClass(el, oldC);
    if (newC && newC.length) addClass(el, newC);
}

function arrayContains(arr, val) {
    if (!arr || !arr.length) return false;
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] === val) return true;
    }
    return false;
}

function toggleClass(el, cls) {
    if (!el) return;
    if (el.className.indexOf(cls) === -1) el.className += ' ' + cls;
    else removeClass(el, cls);
}

function addClass(el, cls) {
    if (!el) return;
    if (el.className.indexOf(cls) === -1) el.className += ' ' + cls;
}

function removeClass(el, cls) {
    if (!el) return;
    var classes = el.className.split(/\s+/);
    for (var i = classes.length - 1; i >= 0; i--) {
        if (classes[i] === cls) classes.splice(i, 1);
    }
    el.className = classes.join(' ');
}


document.addEventListener("DOMContentLoaded", function () {
    // --------------------------
    // Toggle submenu
    // --------------------------
    var submenuLinks = document.querySelectorAll('a[data-toggle="submenu"]');
    for (var i = 0; i < submenuLinks.length; i++) {
        submenuLinks[i].onclick = function (e) {
            e = e || window.event;
            if (e.preventDefault) e.preventDefault(); else e.returnValue = false;
            toggleMenu(this);
        };
    }

    // --------------------------
    // Button actions
    // --------------------------
    setupBtn('.btn-video', function (btn) {
        document.getElementById("video").src = "https://www.youtube.com/embed/" + btn.getAttribute('data-content');
        activerItem(btn.getAttribute('data-icon'));

        openModal('modalVideo');
    });

    setupBtn('.btn-image', function (btn) {
        document.getElementById("img-archi").src = btn.getAttribute('data-content');
        activerItem(btn.getAttribute('data-icon'));

        openModal('modalImage');
    });

    setupBtn('.btn-enigme', function (btn) {
        document.getElementById("img-enigme").src = btn.getAttribute('data-content');
        document.getElementById("img-solution").src = btn.getAttribute('data-solution');
        activerItem(btn.getAttribute('data-icon'));

        openModal('modalEnigme');
    });

    setupBtn('.btn-file', function (btn) {
        loadContent(btn.getAttribute('data-content'), function (data) {
            document.getElementById("modal-file-content").innerHTML = data;
        });
        activerItem(btn.getAttribute('data-icon'));

        openModal('modalFile');
    });

    setupBtn('.btn-question', function (btn) {
        var answer = btn.querySelector(".answer");
        if (answer) answer.style.display = "block";
        replaceClass(btn, "btn-dark", "");
        replaceClass(btn, "btn-question", "social-facebook disabled");
        activerItem(btn.getAttribute('data-icon'));
    });

    setupBtn('.btn-news', function (btn) {
        document.getElementById("modal-news-header").innerHTML = btn.getAttribute('data-title');
        loadContent('/news/' + btn.getAttribute('data-id'), function (data) {
            document.getElementById("modal-news-body").innerHTML = data;
            openModal('modalNews');
        });
        activerItem(btn.getAttribute('data-icon'));
    });

    // --------------------------
    // Initial setup
    // --------------------------
    var savedColor = localStorage.getItem("color");
    if (savedColor) colorer(savedColor);

    var isFr = window.location.href.indexOf('/fr/') !== -1;
    var routes = { 
        '.btn-item-sujet': '/ar/sujets/', 
        '.btn-item-document': '/ar/documents/', 
        '.btn-item-article': '/ar/advices/', 
        '.btn-item-chaine': '/ar/chaines/', 
        '.btn-item-annale': isFr ? '/fr/annales/' : '/ar/annales/'
    };

    for (var sel in routes) {
        if (routes.hasOwnProperty(sel)) {
            var els = document.querySelectorAll(sel);
            for (var i = 0; i < els.length; i++) {
                var el = els[i];
                var id = el.getAttribute('data-id');
                if (id) {
                    el.href = routes[sel] + enc(id);
                    el.removeAttribute('data-id');
                }
            }
        }
    }

    // --------------------------
    // Buttons statut
    // --------------------------
    var btns = document.querySelectorAll(".btn-group-icon");
    for (var i = 0; i < btns.length; i++) {
        var btn = btns[i];
        var id = btn.id;
        if (arrayContains(dzUser.likes, id)) replaceClass(btn, "btn-default", "btn-danger");
        else if (arrayContains(dzUser.dislikes, id)) replaceClass(btn, "btn-default", "btn-warning");
        else if (arrayContains(dzUser.visited, id)) replaceClass(btn, "btn-default", "btn-success");
        else if (localStorage.getItem(id)) replaceClass(btn, "btn-default", localStorage.getItem(id));
    }

    // --------------------------
    // Prevent empty href scroll
    // --------------------------
    var links = document.querySelectorAll('a[href="#"]');
    for (var i = 0; i < links.length; i++) {
        links[i].addEventListener('click', function (e) {
            e.preventDefault ? e.preventDefault() : (e.returnValue = false);
        }, false);
    }
});