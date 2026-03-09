/**
 * Auth Module — User login/registration modal
 * 
 * Include this script AFTER api.js in every HTML page:
 *   <script src="js/api.js"></script>
 *   <script src="js/auth.js"></script>
 * 
 * This script auto-checks login state on page load and shows
 * a login modal if the user is not logged in.
 */

function createLoginModal() {
    // Don't create if already exists
    if (document.getElementById('login-modal')) return;

    const modal = document.createElement('div');
    modal.id = 'login-modal';
    // Fullscreen covering entire body directly without any transparency or blur
    modal.className = 'fixed inset-0 z-[9999] flex flex-col md:flex-row bg-white dark:bg-slate-950 overflow-hidden';
    modal.innerHTML = `
        <!-- Left Side: Branding/Imagery (Hidden on mobile) -->
        <div class="hidden md:flex flex-1 relative bg-primary items-center justify-center p-12 overflow-hidden">
            <!-- Decorative Background Patterns -->
            <div class="absolute inset-0 opacity-10" style="background-image: radial-gradient(circle at 2px 2px, white 1px, transparent 0); background-size: 32px 32px;"></div>
            <div class="absolute -top-32 -left-32 w-96 h-96 bg-accent-yellow rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
            <div class="absolute -bottom-32 -right-32 w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
            
            <div class="relative z-10 text-center max-w-lg">
                <div class="bg-white/10 p-6 rounded-3xl backdrop-blur-md border border-white/20 shadow-2xl inline-block mb-10">
                    <span class="material-symbols-outlined text-8xl text-accent-yellow drop-shadow-lg">school</span>
                </div>
                <h1 class="text-5xl font-black text-white mb-6 leading-tight tracking-tight">dAIgnostix</h1>
                <p class="text-white/80 text-lg leading-relaxed font-light">AI-Powered Diagnostic Tools For Learning</p>
            </div>
        </div>

        <!-- Right Side: Auth Form -->
        <div class="flex-1 flex items-center justify-center p-6 md:p-12 relative h-full overflow-y-auto">
            <div class="w-full max-w-md mx-auto">
                <div class="md:hidden text-center mb-10">
                    <div class="inline-flex items-center justify-center bg-primary/10 p-4 rounded-full mb-4">
                        <span class="material-symbols-outlined text-4xl text-primary">school</span>
                    </div>
                    <h2 class="text-3xl font-black text-slate-900 dark:text-white">dAIgnostix</h2>
                </div>

                <div class="mb-10 text-center md:text-left">
                    <h2 class="text-3xl font-black text-slate-900 dark:text-white mb-2" id="auth-title">Selamat Datang</h2>
                    <p class="text-slate-500 font-medium" id="auth-subtitle">Masuk menggunakan NIP Anda untuk melanjutkan.</p>
                </div>
                
                <!-- Toggle Switch for Login/Register instead of standard tabs -->
                <div class="flex p-1 mb-8 bg-slate-100 dark:bg-slate-800 rounded-xl relative shadow-inner">
                    <div id="auth-tab-indicator" class="absolute top-1 left-1 w-[calc(50%-4px)] h-[calc(100%-8px)] bg-white dark:bg-slate-700 shadow-sm rounded-lg transition-transform duration-300 ease-in-out"></div>
                    <button type="button" id="tab-login" class="flex-1 py-3 text-sm font-bold text-primary dark:text-white z-10 transition-colors">Login</button>
                    <button type="button" id="tab-register" class="flex-1 py-3 text-sm font-bold text-slate-500 dark:text-slate-400 z-10 transition-colors">Daftar Akun</button>
                </div>
                
                <form id="auth-form" class="space-y-5">
                    <div id="field-nama" class="hidden transform transition-all duration-300 opacity-0 -translate-y-4">
                        <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Nama Lengkap</label>
                        <div class="relative">
                            <span class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <span class="material-symbols-outlined text-slate-400">person</span>
                            </span>
                            <input type="text" id="auth-nama" placeholder="Contoh: Budi Santoso"
                                class="w-full pl-11 pr-4 py-3.5 rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:ring-4 focus:ring-primary/20 focus:border-primary transition-all text-sm shadow-sm" />
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">NIP</label>
                        <div class="relative">
                            <span class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <span class="material-symbols-outlined text-slate-400">badge</span>
                            </span>
                            <input type="text" id="auth-nip" required placeholder="Contoh: 198001012005011001"
                                class="w-full pl-11 pr-4 py-3.5 rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:ring-4 focus:ring-primary/20 focus:border-primary transition-all text-sm shadow-sm" />
                        </div>
                    </div>
                    
                    <div id="auth-error" class="hidden transform transition-all duration-300 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 p-4 rounded-r-lg">
                        <div class="flex items-center gap-3">
                            <span class="material-symbols-outlined text-red-500">error</span>
                            <p class="text-sm font-medium text-red-700 dark:text-red-400" id="auth-error-text"></p>
                        </div>
                    </div>

                    <button type="submit" id="auth-btn"
                        class="w-full bg-primary hover:bg-slate-800 text-white py-4 rounded-xl font-black transition-all flex items-center justify-center gap-3 shadow-lg hover:shadow-xl hover:-translate-y-1 mt-6 group">
                        <span id="auth-btn-text">Masuk Sekarang</span>
                        <span class="material-symbols-outlined group-hover:translate-x-1 transition-transform" id="auth-btn-icon">arrow_forward</span>
                    </button>
                </form>

                <div class="mt-12 text-center text-sm text-slate-500">
                    <p>© 2026 Unit Peningkatan dan Pengembangan Aktivitas Instruksional</p>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    let isLoginMode = true;
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const fieldNama = document.getElementById('field-nama');
    const inputNama = document.getElementById('auth-nama');
    const btnText = document.getElementById('auth-btn-text');
    const btnIcon = document.getElementById('auth-btn-icon');
    const tabIndicator = document.getElementById('auth-tab-indicator');
    const authTitle = document.getElementById('auth-title');
    const authSubtitle = document.getElementById('auth-subtitle');
    const errorText = document.getElementById('auth-error-text');
    const errorEl = document.getElementById('auth-error');

    // Add required custom animation classes dynamically to document if missing
    if (!document.getElementById('auth-custom-styles')) {
        const style = document.createElement('style');
        style.id = 'auth-custom-styles';
        style.innerHTML = `
            @keyframes blob {
                0% { transform: translate(0px, 0px) scale(1); }
                33% { transform: translate(30px, -50px) scale(1.1); }
                66% { transform: translate(-20px, 20px) scale(0.9); }
                100% { transform: translate(0px, 0px) scale(1); }
            }
            .animate-blob {
                animation: blob 7s infinite;
            }
            .animation-delay-2000 {
                animation-delay: 2s;
            }
        `;
        document.head.appendChild(style);
    }

    tabLogin.addEventListener('click', () => {
        isLoginMode = true;
        tabIndicator.style.transform = 'translateX(0)';
        tabLogin.className = 'flex-1 py-3 text-sm font-bold text-primary dark:text-white z-10 transition-colors duration-300';
        tabRegister.className = 'flex-1 py-3 text-sm font-bold text-slate-500 dark:text-slate-400 z-10 transition-colors duration-300';

        authTitle.textContent = 'Selamat Datang';
        authSubtitle.textContent = 'Masuk menggunakan NIP Anda untuk melanjutkan.';

        fieldNama.classList.add('opacity-0', '-translate-y-4');
        setTimeout(() => fieldNama.classList.add('hidden'), 300);

        inputNama.removeAttribute('required');
        inputNama.value = '';
        btnText.textContent = 'Masuk Sekarang';
        errorEl.classList.add('hidden');
    });

    tabRegister.addEventListener('click', () => {
        isLoginMode = false;
        tabIndicator.style.transform = 'translateX(100%)';
        tabRegister.className = 'flex-1 py-3 text-sm font-bold text-primary dark:text-white z-10 transition-colors duration-300';
        tabLogin.className = 'flex-1 py-3 text-sm font-bold text-slate-500 dark:text-slate-400 z-10 transition-colors duration-300';

        authTitle.textContent = 'Buat Akun Baru';
        authSubtitle.textContent = 'Daftarkan data diri Anda untuk memulai pembelajaran.';

        fieldNama.classList.remove('hidden');
        // Trigger animation next frame
        requestAnimationFrame(() => {
            fieldNama.classList.remove('opacity-0', '-translate-y-4');
        });

        inputNama.setAttribute('required', 'true');
        btnText.textContent = 'Daftar Akun';
        errorEl.classList.add('hidden');
    });

    // Handle form submission
    document.getElementById('auth-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const nip = document.getElementById('auth-nip').value.trim();
        const btn = document.getElementById('auth-btn');

        errorEl.classList.add('hidden');

        if (!nip) {
            errorText.textContent = 'NIP wajib diisi';
            errorEl.classList.remove('hidden');
            return;
        }

        btn.disabled = true;
        const origBtnHtml = btn.innerHTML;
        btn.innerHTML = `<svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Memproses...`;

        try {
            let userData;
            if (isLoginMode) {
                try {
                    userData = await getUser(nip);
                } catch (err) {
                    if (err.message === "User tidak ditemukan" || err.message.includes("404")) {
                        throw new Error("NIP belum terdaftar, silakan pilih tab Register.");
                    }
                    throw err;
                }
            } else {
                const nama = inputNama.value.trim();
                if (!nama) throw new Error("Nama lengkap wajib diisi untuk registrasi");
                const registerResponse = await registerUser(nip, nama);
                if (registerResponse.message === "User sudah terdaftar") {
                    throw new Error("NIP sudah terdaftar, silakan pilih tab Login.");
                }
                userData = registerResponse.user;
            }

            const role = userData.role || 'user';
            setCurrentUser(userData.nip, userData.nama, role);

            // Get progress state from API
            const status = await getUserStatus(nip);
            // State is now read directly from API by each page on load

            // Close modal
            modal.remove();

            // Role-based redirect
            if (role === 'admin') {
                window.location.href = 'admin.html';
            } else {
                window.location.reload();
            }
        } catch (err) {
            errorText.textContent = err.message || 'Terjadi kesalahan. Periksa koneksi ke server.';
            errorEl.classList.remove('hidden');
            btn.disabled = false;
            btn.innerHTML = origBtnHtml;
        }
    });
}

// Auto-check on page load
document.addEventListener('DOMContentLoaded', async () => {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';

    if (!isLoggedIn()) {
        // If on admin page without login, redirect to index
        if (currentPage === 'admin.html') {
            window.location.href = 'index.html';
            return;
        }
        createLoginModal();
    } else {
        // Protect admin page — only admin can access
        if (currentPage === 'admin.html' && !isAdmin()) {
            await customAlert('Akses ditolak. Halaman ini hanya untuk Admin.', 'Terlarang');
            window.location.href = 'index.html';
            return;
        }

        // Update user display elements
        const nip = getCurrentNip();
        const nama = getCurrentNama();

        // Update any element with data-user-name attribute
        document.querySelectorAll('[data-user-name]').forEach(el => {
            el.textContent = nama;
        });
        document.querySelectorAll('[data-user-nip]').forEach(el => {
            el.textContent = nip;
        });
    }
});

function handleLogout() {
    // Only build custom CSS modal if doesn't exist
    if (document.getElementById('custom-logout-modal')) return;

    const logoutModal = document.createElement('div');
    logoutModal.id = 'custom-logout-modal';
    logoutModal.className = 'fixed inset-0 z-[99999] flex items-center justify-center bg-slate-900/60 backdrop-blur-md opacity-0 transition-opacity duration-300';
    logoutModal.innerHTML = `
        <div class="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl p-8 max-w-sm w-full mx-4 transform scale-95 opacity-0 transition-all duration-300" id="logout-modal-content">
            <div class="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-6 shadow-sm border border-red-200 dark:border-red-900/50">
                <span class="material-symbols-outlined text-3xl text-red-500">logout</span>
            </div>
            <h3 class="text-2xl font-black text-center text-slate-900 dark:text-white mb-2">Keluar Akun?</h3>
            <p class="text-center text-slate-500 dark:text-slate-400 mb-8 font-medium text-sm">Anda akan keluar dari sesi pembelajaran dAIgnostix.</p>
            
            <div class="flex gap-3">
                <button id="btn-cancel-logout" class="flex-1 py-3.5 px-4 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 outline-none text-slate-700 dark:text-slate-200 font-bold rounded-xl transition-colors">
                    Batal
                </button>
                <button id="btn-confirm-logout" class="flex-1 py-3.5 px-4 bg-red-500 hover:bg-red-600 text-white font-bold rounded-xl shadow-lg shadow-red-500/30 transition-all hover:-translate-y-0.5 outline-none">
                    Ya, Keluar
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(logoutModal);

    // Trigger open animation
    requestAnimationFrame(() => {
        logoutModal.classList.remove('opacity-0');
        const content = document.getElementById('logout-modal-content');
        content.classList.remove('scale-95', 'opacity-0');
        content.classList.add('scale-100', 'opacity-100');
    });

    const closeLogoutModal = () => {
        logoutModal.classList.add('opacity-0');
        const content = document.getElementById('logout-modal-content');
        content.classList.remove('scale-100', 'opacity-100');
        content.classList.add('scale-95', 'opacity-0');
        setTimeout(() => logoutModal.remove(), 300);
    };

    document.getElementById('btn-cancel-logout').addEventListener('click', closeLogoutModal);

    // Close on background click
    logoutModal.addEventListener('click', (e) => {
        if (e.target === logoutModal) closeLogoutModal();
    });

    document.getElementById('btn-confirm-logout').addEventListener('click', () => {
        clearCurrentUser();
        window.location.href = 'index.html';
    });
}
