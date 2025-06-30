# Yarışmacılar için Örnek Sunucu Bağlantı Arayüzü
Bu repository Teknofest Havacılıkta Yapay Zeka yarışması değerlendirme sunucusuna (THYZDS) örnek bağlantının kurulması için geliştirilmiştir.
Yarışmacılar örnek arayüzü ihtiyaçlarına göre güncelleyebilir ya da farklı bir dil ile (C++, vs) benzerini entegre edebilirler.
 

# Kurulum
- Sistem için bir sanal ortam oluşturulur. (Anaconda'nın kurulu olduğu varsayılmaktadır.)
```shell
$ conda create -n teknofest_yarisma python=3.7
$ conda activate teknofest_yarisma
```
- Gerekli paketler yüklenir.
```shell
$ pip install -r requirements.txt
```
- `./config` klasorü altında bulunan `example.env` klasörü referans alınarak (kopyalanarak) `.env` isminde bir dosya oluşturulur.
- `.env` dosyasının içeriği teknofest tarafından verilen takım kullanıcı adı ve şifreleri ile güncellenerek kaydedilir. (Dikkat: Sonuçta oluşacak dosyanın yolu `./config/.env` şeklinde olacaktır.) 
````text
TEAM_NAME=takim_adi
PASSWORD=sifre
EVALUATION_SERVER_URL="SERVER BILGISI SUNUCU ACILDIGINDA YARISMACILAR ILE PAYLASILACAKTIR"
SESSION_NAME=oturum_ismi
````
- Kod içerisinde yorumlar dikkate alınarak gerekli düzenlemeler ve geliştirmeler yapılır. 
  ```
  NOT: 
  İlk testinizde sadece `.env` dosyasında değişiklik yaparak sunucu iletişiminizi test edebilirsiniz. 
  ```
- Sistemi çalıştırmak için aşağıdaki komut çalıştırılır.
````shell
python main.py
````
# Yarışmacıların Modellerini Tanımlayacakları Kısımlar
Yarışmacılar sağlanan sunucu haberleşme arayüzüne ait kodları modifiye etmeden, yanlızca ```object_detection_model.py``` içerisinde değişiklik yaparak modellerini sisteme entegre edebilirler.
Geliştirilen modellerin ``ObjectDetectionModel`` sınıfına entegrasyonu ile ilgili detaylar kod içerisinde yorumlar ile belirtilmiştir. Yarışmacılar nesne tespiti ve pozisyon kestirimi için geliştirdikleri algoritmalarını yorumlara bakarak ilgili yerlere entegre edebilirler.

## Logların İncelenmesi
Sistem çalışma esnasında gerçekleştirdiği işlemleri `_logs` klasörü altında kayıt altına almaktadır. Sistem hataları bu log dosyaları üzerinden takip edilebilir. Yarışma esnasında yapılacak itirazlarda log dosyası içeriği değerlendirmeye alınacaktır.

# Sorumluluk Beyanı
Bu sistem yarışmacılar için referans olarak sunulmuştur. Bu sistemi kullanmak kullanıcıların tercihine bağlıdır. Sağlanan sistem dolayısı ile oluşabilecek problemler yarışmacıların sorumluluğundadır.
Yarışmacı takımlar sunucu ile sağlıklı iletişim kuracak yapıyı geliştirmek/test etmek sorumluluğundadır. Teknofest, sistemde değişiklik yapma hakkını saklı tutar.