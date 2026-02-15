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

function openProfile() {
    profileModal?.classList.remove("hidden");
    document.body.style.overflow = "hidden";
    lucide?.createIcons?.();
}

function closeProfile() {
    profileModal?.classList.add("hidden");
    document.body.style.overflow = "";
}

profileBtn?.addEventListener("click", openProfile);
profileClose?.addEventListener("click", closeProfile);
profileOk?.addEventListener("click", closeProfile);

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