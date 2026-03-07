saya ingin membuat platform pembelajaran elearning dengan artificial intelligence melalui sebuah web e learning saya. ini digunakan untuk mempermudah user belajar dengan adanya learning path

berikut alur kerja nya. 

1. admin akan menyediakan materi pembelajaran berupa PDF. menggunakan RAG, supaya AI tidak halusinasi  
2. kemudian user akses e learning tersebut, dan membuka homepage (elearning berupa html saja biar gampang), web akan mengecek apakah user sudah memiliki database atau belum ,jika sudah punya maka gunakan data user dari database seperti apakah sudah menyelesaikan pretest, berapa nilai pretest, menyelesaikan materi bab apa saja, apakah sudah ada learning path nya, apakah sudah melakukan posttest dan apakah sudah ada nilai posttest, soal posttest dan pretest beserta jawabannya. jika belum maka masukkan data awal user seperti nama dll ke dalam database.  
3. User masuk ke page pretest kemudian karena mendapat input dari user, web akan mengecek, apakah user tersebut sudah memiliki database, jika sudah ambil data dari database, termasuk soal pretest. Jika user belum memiliki data pretest maka,  AI akan membuat soal pretest dari materi PDF yang disediakan sebelumnya (hasil berupa json). Dan mengirim ke user dan database untuk disimpan. Jika di database user sudah memiliki data pretest maka akan ditampilkan ke web, tanpa perlu ai membuat soal pretest lagi. berikan animasi loading sambil menunggu data dari AI soal pretest ada 30 soal  
4. user mengerjakan pretest.   
5. hasil dari pretest dikirim ke database dan ke AI untuk menentukan learning path yang sesuai pre test user (profil pengetahuan user). Web akan mengecek apakah user sudah punya data learning path atau belum, jika sudah maka ambil data learning path tersebut. Jika belum maka AI akan membuatkan (json) learning path untuk user tersebut dan mengirimkannya ke web dan database. misal user kurang di bab 4 dan sudah bagus di bab 1 2 3\. kemudian AI menentukan learning path user, yaitu fokus di bab 4\.   
6. Setelah user selesai pretest maka user akan menuju ke page learning path, dan membaca learning path  
7. Pada learning path akan terdapat shortcut ke page masing masing materi misal bab 1 2 3 4 dan posttest  
8. User menuju page materi dan belajar mandiri. Setiap page memiliki event listener untuk data keaktifan user. Berupa page apa yang di kunjungi dan berapa lama dia belajar itu.  
9. Setelah mengerjakan materi, user dapat menuju ke page posttest.   
10. Pada page posttest  web akan mengecek, apakah user tersebut sudah memiliki database, jika sudah ambil data dari database, termasuk soal posttest, dan nilai postest. Jika user belum memiliki data posttest maka,  AI akan membuat soal postest dari materi PDF yang disediakan sebelumnya (hasil berupa json). Dan mengirim ke user dan database untuk disimpan. Jika di database user sudah memiliki data posttest maka akan ditampilkan ke web, tanpa perlu ai membuat soal postest lagi.berikan animasi loading sambil menunggu data dari AI. soal nya 30  
11. Jika user telah menyelesaikan posttest maka simpan hasil nilai ke database.   
12. Setelah itu user menuju page feedback. web akan mengecek, apakah user tersebut sudah memiliki database, jika sudah ambil data dari database, termasuk hasil feedback. Jika user belum memiliki data feedback maka,  AI akan membuat feedback dari database hasil pretest posttest, learning path, event listener dan waktu pengerjaan tiap page/bab. (hasil berupa json). Dan mengirim ke user dan database untuk disimpan. Jika di database user sudah memiliki data feedback maka akan ditampilkan ke web, tanpa perlu ai membuat feedback lagi.berikan animasi loading sambil menunggu data dari AI  
    

Yang perlu diperhatikan. 

1. Perlu menggunakan database
2. Perlu RAG  dan AI
3. Sudah punya UI, sehingga ai hanya perlu membuat json dan mudah menampilkan hasil AI ke web

List database 

1. Nama  
2. NIP  
3. Pretest  
   1. Soal  
   2. Jawaban  
   3. Nilai pretest  
4. Learning path  
   1. Profil  
   2. Penjabaran profil  
5. Materi  
   1. Bab 1 finish or not  
   2. Bab 2 finish or not  
   3. Bab 3 finish or not  
   4. Bab 4 finish or not  
   5. Beberapa Event listener waktu yang digunakan user untuk belajar tiap page (dinamis sesuai banyak nya page)   
6. Postest  
   1. Soal  
   2. Jawaban  
   3. Nilai postest  
7. Feedback   
   1. Profil akhir
   2. Analisis Perkembangan Kompetensi
   3. Evaluasi Perilaku Belajar (Live Event Tracker Analysis)  
   4. Transformasi Klasifikasi Profil
   5. Kesimpulan Strategis & Next Actions

Penting, kamu perlu membuat konsep proposal project ini, secara teknis, prioritas gunakan service gratis, bisa berbayar jika gratis tidak ada/sulit. jika perlu setting database atau yang lainnnya yang tidak bisa kamu lakukan sendiri buat file tutorial lengkap nya 

