/**
 * API Client Module
 * Centralized API communication for all frontend pages.
 * 
 * Include this script in every HTML page:
 *   <script src="js/api.js"></script>
 */

// ============== KONFIGURASI ==============
// Untuk development lokal:
// const API_BASE_URL = 'http://localhost:8000/api';

// Untuk production (ganti dengan URL Railway Anda):
const API_BASE_URL = 'https://daignostic-production.up.railway.app/api';

// ============== HELPER ==============

async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) options.body = JSON.stringify(body);

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || `API Error: ${response.status}`);
        }
        return data;
    } catch (error) {
        console.error(`API Error [${method} ${endpoint}]:`, error);
        throw error;
    }
}

async function apiUpload(endpoint, file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            body: formData,
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || `Upload Error: ${response.status}`);
        }
        return data;
    } catch (error) {
        console.error(`Upload Error [${endpoint}]:`, error);
        throw error;
    }
}

// ============== USER API ==============

async function registerUser(nip, nama) {
    return apiCall('/user/register', 'POST', { nip, nama });
}

async function getUser(nip) {
    return apiCall(`/user/${nip}`);
}

async function getUserStatus(nip) {
    return apiCall(`/user/${nip}/status`);
}

// ============== PRETEST API ==============

async function getPretest(nip) {
    return apiCall(`/pretest/${nip}`);
}

async function submitPretest(nip, jawaban) {
    return apiCall(`/pretest/${nip}/submit`, 'POST', { jawaban });
}

// ============== LEARNING PATH API ==============

async function getLearningPath(nip) {
    return apiCall(`/learning-path/${nip}`);
}

// ============== MATERI API ==============

async function getMateriProgress(nip) {
    return apiCall(`/materi/${nip}/progress`);
}

async function trackEvent(nip, page, action, durationSeconds = 0) {
    return apiCall(`/materi/${nip}/track`, 'POST', {
        page,
        action,
        duration_seconds: durationSeconds,
    });
}

async function trackTime(nip, bab, seconds) {
    return apiCall(`/materi/${nip}/time`, 'POST', { bab, seconds });
}

async function completeBab(nip, bab) {
    return apiCall(`/materi/${nip}/complete/${bab}`, 'POST');
}

// ============== PUBLIC CONFIG / BAB API ==============

async function getPublicConfig() {
    return apiCall('/materi/config');
}

async function getPublicBabList() {
    return apiCall('/materi/bab-list');
}

// ============== POSTTEST API ==============

async function getPosttest(nip) {
    return apiCall(`/posttest/${nip}`);
}

async function submitPosttest(nip, jawaban) {
    return apiCall(`/posttest/${nip}/submit`, 'POST', { jawaban });
}

// ============== FEEDBACK API ==============

async function getFeedback(nip) {
    return apiCall(`/feedback/${nip}`);
}

// ============== ADMIN API ==============

async function getAdminConfig() {
    return apiCall('/admin/config');
}

async function saveAdminConfig(judul, deskripsi) {
    return apiCall('/admin/config', 'POST', { judul, deskripsi });
}

async function getAdminBab() {
    return apiCall('/admin/bab');
}

async function addAdminBab(nomor, judul, deskripsi = '') {
    return apiCall('/admin/bab', 'POST', { nomor, judul, deskripsi });
}

async function updateAdminBab(babId, nomor, judul, deskripsi = '') {
    return apiCall(`/admin/bab/${babId}`, 'PUT', { nomor, judul, deskripsi });
}

async function deleteAdminBab(babId) {
    return apiCall(`/admin/bab/${babId}`, 'DELETE');
}

async function uploadBabPdf(babId, file) {
    return apiUpload(`/admin/bab/${babId}/upload-pdf`, file);
}

async function uploadBabMateriPdf(babId, file) {
    return apiUpload(`/admin/bab/${babId}/upload-materi-pdf`, file);
}

async function reindexBab(babId) {
    return apiCall(`/admin/reindex-bab/${babId}`, 'POST');
}

async function getAdminUsers() {
    return apiCall('/admin/users');
}

async function getAdminUserDetail(nip) {
    return apiCall(`/admin/users/${nip}/detail`);
}

async function updateUserRole(nip, role) {
    return apiCall(`/admin/users/${nip}/role`, 'PUT', { role });
}

async function deleteAdminUser(nip) {
    return apiCall(`/admin/users/${nip}`, 'DELETE');
}

async function getDbOverview() {
    return apiCall('/admin/db-overview');
}

async function clearVectors() {
    return apiCall('/admin/vectors', 'DELETE');
}

// ============== BANK SOAL API (Admin) ==============

async function generateBankSoal(babId = null) {
    const url = babId ? `/admin/bank-soal/generate?bab_id=${babId}` : '/admin/bank-soal/generate';
    return apiCall(url, 'POST');
}

async function getAdminBankSoal() {
    return apiCall('/admin/bank-soal');
}

async function updateBankSoal(bankId, soal, status = 'draft') {
    return apiCall(`/admin/bank-soal/${bankId}`, 'PUT', { soal, status });
}

async function publishBankSoal(bankId) {
    return apiCall(`/admin/bank-soal/${bankId}/publish`, 'POST');
}

// ============== QUIZ API (User) ==============

async function getQuiz(nip, babNomor) {
    return apiCall(`/quiz/${nip}/${babNomor}`);
}

async function submitQuiz(nip, babNomor, jawaban) {
    return apiCall(`/quiz/${nip}/${babNomor}/submit`, 'POST', { jawaban });
}

// ============== UTILITY ==============

function getCurrentNip() {
    return localStorage.getItem('userNip') || '';
}

function getCurrentNama() {
    return localStorage.getItem('userName') || '';
}

function getCurrentRole() {
    return localStorage.getItem('userRole') || 'user';
}

function setCurrentUser(nip, nama, role = 'user') {
    localStorage.setItem('userNip', nip);
    localStorage.setItem('userName', nama);
    localStorage.setItem('userRole', role || 'user');
}

function clearCurrentUser() {
    localStorage.removeItem('userNip');
    localStorage.removeItem('userName');
    localStorage.removeItem('userRole');
    localStorage.removeItem('progressState');
}

function isLoggedIn() {
    return !!getCurrentNip();
}

function isAdmin() {
    return getCurrentRole() === 'admin';
}

// ============== MODALS UTILITY ==============

function customAlert(message, title = 'Informasi') {
    return new Promise(resolve => {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-[99999] flex items-center justify-center bg-slate-900/60 backdrop-blur-md opacity-0 transition-opacity duration-300';
        modal.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl p-8 max-w-sm w-full mx-4 transform scale-95 opacity-0 transition-all duration-300 text-center flex flex-col items-center">
                <div class="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mb-6 shadow-sm border border-blue-200 dark:border-blue-900/50">
                    <span class="material-symbols-outlined text-3xl text-primary dark:text-blue-400">info</span>
                </div>
                <h3 class="text-2xl font-black text-slate-900 dark:text-white mb-2">${title}</h3>
                <p class="text-slate-500 dark:text-slate-400 mb-8 font-medium text-sm">${message}</p>
                <button class="w-full py-3.5 px-4 bg-primary hover:bg-slate-800 text-white font-bold rounded-xl shadow-lg transition-all hover:-translate-y-0.5 outline-none custom-modal-ok">
                    Mengerti
                </button>
            </div>
        `;
        document.body.appendChild(modal);

        requestAnimationFrame(() => {
            modal.classList.remove('opacity-0');
            modal.children[0].classList.remove('scale-95', 'opacity-0');
            modal.children[0].classList.add('scale-100', 'opacity-100');
        });

        const close = () => {
            modal.classList.add('opacity-0');
            modal.children[0].classList.remove('scale-100', 'opacity-100');
            modal.children[0].classList.add('scale-95', 'opacity-0');
            setTimeout(() => { modal.remove(); resolve(); }, 300);
        };

        modal.querySelector('.custom-modal-ok').addEventListener('click', close);
    });
}

function customConfirm(message, title = 'Konfirmasi', confirmText = 'Ya', cancelText = 'Batal') {
    return new Promise(resolve => {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-[99999] flex items-center justify-center bg-slate-900/60 backdrop-blur-md opacity-0 transition-opacity duration-300';
        modal.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl p-8 max-w-sm w-full mx-4 transform scale-95 opacity-0 transition-all duration-300 text-center flex flex-col items-center">
                <div class="w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center mb-6 shadow-sm border border-yellow-200 dark:border-yellow-900/50">
                    <span class="material-symbols-outlined text-3xl text-yellow-500 dark:text-yellow-400">help</span>
                </div>
                <h3 class="text-2xl font-black text-slate-900 dark:text-white mb-2">${title}</h3>
                <p class="text-slate-500 dark:text-slate-400 mb-8 font-medium text-sm">${message}</p>
                <div class="flex gap-3 w-full">
                    <button class="flex-1 py-3.5 px-4 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-bold rounded-xl transition-colors outline-none custom-modal-cancel">
                        ${cancelText}
                    </button>
                    <button class="flex-1 py-3.5 px-4 bg-primary hover:bg-slate-800 text-white font-bold rounded-xl shadow-lg transition-all hover:-translate-y-0.5 outline-none custom-modal-confirm">
                        ${confirmText}
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        requestAnimationFrame(() => {
            modal.classList.remove('opacity-0');
            modal.children[0].classList.remove('scale-95', 'opacity-0');
            modal.children[0].classList.add('scale-100', 'opacity-100');
        });

        const close = (result) => {
            modal.classList.add('opacity-0');
            modal.children[0].classList.remove('scale-100', 'opacity-100');
            modal.children[0].classList.add('scale-95', 'opacity-0');
            setTimeout(() => { modal.remove(); resolve(result); }, 300);
        };

        modal.querySelector('.custom-modal-cancel').addEventListener('click', () => close(false));
        modal.querySelector('.custom-modal-confirm').addEventListener('click', () => close(true));
        modal.addEventListener('click', (e) => { if (e.target === modal) close(false); });
    });
}
