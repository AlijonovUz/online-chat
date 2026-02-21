lucide?.createIcons?.();

const search = document.getElementById("search");
const clearBtn = document.getElementById("clearSearch");
const box = document.getElementById("searchBox");
const resultsEl = document.getElementById("searchResults");

const profileBtn = document.getElementById("profileBtn");
const profileModal = document.getElementById("profileModal");
const profileClose = document.getElementById("profileClose");
const profileOk = document.getElementById("profileOk");

let timer = null;

const profileViewBox = document.getElementById("profileViewBox");
const profileEditBox = document.getElementById("profileEditBox");

const profileEditBtnInModal = document.getElementById("profileEditBtnInModal");
const profileEditCancel = document.getElementById("profileEditCancel");

(() => {
  const menu = document.getElementById("chatCtxMenu");
  const form = document.getElementById("chatDeleteForm");
  if (!menu || !form) return;

  let currentRow = null;
  let longPressTimer = null;
  let longPressFired = false;

  function hideMenu() {
    menu.classList.add("hidden");
    currentRow = null;
  }

  function clamp(n, min, max) { return Math.max(min, Math.min(max, n)); }

  function showMenuAt(x, y, row) {
    currentRow = row;
    menu.classList.remove("hidden");
    lucide?.createIcons?.();

    const rect = menu.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    const left = clamp(x, 8, vw - rect.width - 8);
    const top  = clamp(y, 8, vh - rect.height - 8);

    menu.style.left = left + "px";
    menu.style.top  = top + "px";
  }

  document.addEventListener("contextmenu", (e) => {
    const row = e.target.closest(".user-row");
    if (!row) return;
    e.preventDefault();
    showMenuAt(e.clientX, e.clientY, row);
  });

  document.addEventListener("pointerdown", (e) => {
    const row = e.target.closest(".user-row");
    if (!row) return;
    if (e.pointerType === "mouse") return;

    longPressFired = false;
    clearTimeout(longPressTimer);

    longPressTimer = setTimeout(() => {
      longPressFired = true;
      showMenuAt(e.clientX || (window.innerWidth / 2), e.clientY || 80, row);
      navigator.vibrate?.(10);
    }, 550);
  }, { passive: true });

  document.addEventListener("pointerup", () => clearTimeout(longPressTimer));
  document.addEventListener("pointermove", () => clearTimeout(longPressTimer));

  document.addEventListener("click", (e) => {
    const row = e.target.closest(".user-row");
    if (row && longPressFired) {
      e.preventDefault();
      longPressFired = false;
      return;
    }
    if (!menu.classList.contains("hidden") && !e.target.closest("#chatCtxMenu")) hideMenu();
  });

  document.addEventListener("keydown", (e) => { if (e.key === "Escape") hideMenu(); });

  menu.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn || !currentRow) return;

    const action = btn.dataset.action;
    const href = currentRow.getAttribute("href");
    const delUrl = currentRow.dataset.deleteUrl;

    if (action === "open") {
      window.location.href = href;
      return;
    }

    if (action === "delete") {
      hideMenu();
      if (!delUrl) return;
      form.action = delUrl;
      form.submit();
    }
  });

  window.addEventListener("scroll", hideMenu, { passive: true });
  window.addEventListener("resize", hideMenu);
})();

function openProfileEdit() {
    profileViewBox?.classList.add("hidden");
    profileEditBox?.classList.remove("hidden");
    lucide?.createIcons?.();
}

function closeProfileEdit() {
    profileEditBox?.classList.add("hidden");
    profileViewBox?.classList.remove("hidden");
    lucide?.createIcons?.();
}

function openProfile() {
    profileModal?.classList.remove("hidden");
    document.body.style.overflow = "hidden";
    lucide?.createIcons?.();
}

function closeProfile() {
    profileModal?.classList.add("hidden");
    document.body.style.overflow = "";

    profileEditBox?.classList.add("hidden");
    profileViewBox?.classList.remove("hidden");
}

profileBtn?.addEventListener("click", openProfile);
profileClose?.addEventListener("click", closeProfile);
profileOk?.addEventListener("click", closeProfile);

profileEditBtnInModal?.addEventListener("click", openProfileEdit);
profileEditCancel?.addEventListener("click", closeProfileEdit);

profileModal?.addEventListener("click", (e) => {
    if (e.target === profileModal || e.target === profileModal.firstElementChild) closeProfile();
});

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && profileModal && !profileModal.classList.contains("hidden")) closeProfile();
});

function renderResults(items) {
    if (!items.length) {
        resultsEl.innerHTML = `<div class="p-4 text-sm text-slate-500">Foydalanuvchi topilmadi.</div>`;
        return;
    }

    resultsEl.innerHTML = items.map(u => `
      <a href="/chats/${u.username}/"
         class="flex items-center justify-between gap-3 px-4 py-3 hover:bg-slate-50 transition">
        <div class="min-w-0">
          <div class="flex items-center gap-1 min-w-0">
            <div class="truncate font-medium text-slate-900">${u.name}</div>
            ${u.is_verified ? `
              <svg class="w-[14px] h-[14px] shrink-0 block" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" fill="#3390EC"></circle>
                <path d="M8 12.5L10.2 14.7L16 9"
                      stroke="white" stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"></path>
              </svg>` : ``}
          </div>
          <div class="text-xs text-slate-500 truncate">@${u.username}</div>
        </div>
        ${u.online ? `<span class="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">onlayn</span>` : ``}
      </a>
    `).join("");
}

async function doSearch(q) {
    try {
        const res = await fetch(`/search/?q=${encodeURIComponent(q)}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        renderResults(data.results || []);
        box.classList.remove("hidden");
    } catch (err) {
        resultsEl.innerHTML = `<div class="p-4 text-sm text-rose-600">Search error: ${err.message}</div>`;
        box.classList.remove("hidden");
    }
}

search?.addEventListener("input", () => {
    const q = search.value.trim();

    clearBtn?.classList.toggle("hidden", !search.value.length);

    clearTimeout(timer);

    if (q.length < 2) {
        box?.classList.add("hidden");
        return;
    }

    timer = setTimeout(() => doSearch(q), 250);
});

document.addEventListener("click", (e) => {
    if (box && search && !box.contains(e.target) && e.target !== search) {
        box.classList.add("hidden");
    }
});

clearBtn?.addEventListener("click", () => {
    if (!search) return;
    search.value = "";
    box?.classList.add("hidden");
    clearBtn.classList.add("hidden");
    search.focus();
});