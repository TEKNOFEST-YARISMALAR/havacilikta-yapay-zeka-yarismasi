# Takım Bağlantı Arayüzü — Kullanım Kılavuzu

Bu kılavuz, yarışmaya katılacak bir takımın arayüzü **sıfırdan** çalıştırması ve **kendi modelini** entegre etmesi için hazırlanmıştır. Sıralı şekilde takip etmeniz yeterlidir.

---

## 1. Bu arayüz ne yapar?

Arayüz, değerlendirme sunucusuna bağlanır ve şunları **sizin yerinize otomatik** yapar:
- Sunucuya giriş yapar (token alır),
- Kareleri (frame) **birer birer** çeker ve diske indirir,
- Sizin modelinizin ürettiği tahmini sunucuya gönderir,
- Bir sonraki kareye geçer; bağlantı koparsa **kaldığı yerden** devam eder.

Sizin tek yapmanız gereken: **kendi modelinizi tek bir dosyaya bağlamak.** Geri kalan her şey hazırdır.

Üç görev vardır:
- **Görev 1 — Nesne Tespiti:** Karedeki nesneleri bul (sınıf + iniş durumu + hareket durumu + kutu).
- **Görev 2 — Konum Kestirimi:** Uydu/GPS verisi sağlıksızken aracın konumunu (x, y, z) tahmin et.
- **Görev 3 — Referans Nesne Tespiti:** Sunucunun verdiği referans görüntüsünü, ilgili karelerde bul (kutu).

---

## 2. Kurulum

> Python **3.12** ve Anaconda kurulu olduğu varsayılır.

```shell
conda create -n teknofest_yarisma python=3.12
conda activate teknofest_yarisma
pip install -r requirements.txt
```

---

## 3. Giriş bilgilerinizi yazın → `config/.env`

1. `config/example.env` dosyasını kopyalayıp adını **`.env`** yapın. Son yol şu olmalı: **`config/.env`**
2. İçini Teknofest'in size verdiği bilgilerle doldurun:

```text
TEAM_NAME=takim_kullanici_adiniz
PASSWORD=takim_sifreniz
EVALUATION_SERVER_URL="https://...."   # Sunucu açıldığında sizinle paylaşılacaktır. 
SESSION_NAME=oturum_ismi               # (Kullanılmıyor; boş kalabilir, otomatik algılanır)
```

| `EVALUATION_SERVER_URL` | Sunucu adresi (sonunda **`/`** olmalı)


> `.env` dosyanızı kimseyle paylaşmayın, herkese açık bir depoya (GitHub vb.) yüklemeyin.

---

## 4. Önce bağlantınızı test edin (tahmin GÖNDERMEDEN)

> **ÇOK ÖNEMLİ:** Sunucu her kare için **yalnızca BİR kez** tahmin kabul eder. Bir kareye tahmin gönderdikten sonra **üzerine tekrar gönderemezsiniz** (sunucu `406` hatası verir). Bu yüzden **modeliniz hazır olmadan** gerçek (puanlanan) oturumda `python main.py` **çalıştırmayın**; aksi halde örnek/rastgele tahminler kalıcı kaydedilir ve o karelerin puanı sabitlenir — geri alınamaz.
> Bağlantınızı test oturumlarında test edebilirsiniz.

---

## 5. Kendi modelinizi entegre edin → **SADECE** `src/object_detection_model.py`

> **Yalnızca bu dosyayı** düzenleyin. Diğer dosyalara dokunmayın (bkz. Bölüm 8).

Tüm işiniz `detect()` fonksiyonunun içindedir. Bu fonksiyon **her kare için** çağrılır ve elinizde şunlar hazırdır:
- `frame_image_path` → **indirilmiş kare görüntüsünün diskteki yolu** (modelinize bunu verin),
- `health_status` → `'0'` (sağlıksız), `'1'` (sağlam) veya `None` (çeviri yok),
- `active_refs` ve `ref_image_paths` → Görev 3 için aktif referanslar ve görüntü yolları.

### Görev 1 — Nesne Tespiti

Örnekteki `for i in range(1, 3):` döngüsünü **silin** ve yerine kendi model çıktınızı koyun. Her tespit için bir `DetectedObject` ekleyin:

```python
# results = self.model(frame_image_path)   # kendi modelinizi çalıştırın
for det in results:                          # kendi tespitleriniz
    cls = classes["Tasit"],                  # SONDAKİ VİRGÜL ŞART (tuple olmalı!)
    landing_status = landing_statuses["Inis Alani Degil"]
    moving_status  = moving_statuses["Hareketli"]   # yalnızca "Tasit" için anlamlı
    top_left_x     = det.x1                  # kutunun sol-üst x'i (piksel)
    top_left_y     = det.y1                  # kutunun sol-üst y'si
    bottom_right_x = det.x2                  # kutunun sağ-alt x'i
    bottom_right_y = det.y2                  # kutunun sağ-alt y'si

    prediction.add_detected_object(
        DetectedObject(cls, landing_status, moving_status,
                       top_left_x, top_left_y, bottom_right_x, bottom_right_y)
    )
```

> **En sık yapılan hata:** `cls = classes["Tasit"]` yazmak. Sondaki **virgülü unutmayın** → `cls = classes["Tasit"],` Aksi halde program hata verir.

### Görev 2 — Konum Kestirimi (Translation)

**`health_status == '0'`** (uydu/GPS verisi yok) durumunda kendi kestiriminizi gönderebilirsiniz.
**`health_status == '1'`** (uydu/GPS verisi var) durumunda GT değerini veya kendi kestiriminizi sunucuya gönderebilirsiniz.

```python
if health_status == '0':                 # veri YOK → siz tahmin edin
    pred_translation_x = ...             # kendi x kestiriminiz
    pred_translation_y = ...             # kendi y kestiriminiz
    pred_translation_z = ...             # kendi z kestiriminiz
    prediction.add_translation_object(
        DetectedTranslation(pred_translation_x, pred_translation_y, pred_translation_z)
    )
```

### Görev 3 — Referans Nesne Tespiti

Örnekteki sabit `bbox = (10.0, 10.0, 120.0, 120.0)` satırını kendi sonucunuzla değiştirin. Pencere kontrolünü **olduğu gibi bırakın**:

```python
for ref in (active_refs or []):
    start_img = ref.get('frame_start_image_url', '')
    end_img   = ref.get('frame_end_image_url', '')
    if not (start_img and end_img and start_img <= prediction.image_url <= end_img):
        continue

    ref_path = ref_image_paths.get(ref['url'])    # referans görüntüsünün diskteki yolu
    # bbox = self.match(ref_path, frame_image_path)   # referansı bu karede bulun
    bbox = (x1, y1, x2, y2)                        # kendi kutunuz (piksel)

    prediction.add_reference_prediction(
        ReferencePrediction(ref['url'], prediction.frame_url, *bbox)
    )
```

> İsterseniz görüntü ön-işleme (resize, normalize vb.) için aynı dosyadaki `process()` fonksiyonuna da kod ekleyebilirsiniz.

---

## 6. Sınıf ve durum kodları (`src/constants.py` — **DEĞİŞTİRMEYİN**)

Değerleri her zaman bu sözlükler üzerinden kullanın (elle "0", "1" yazmayın):

**Sınıflar** (`classes`)
| İsim | Değer |
|---|---|
| `Tasit` | 0 |
| `Insan` | 1 |
| `UAP` | 2 |
| `UAI` | 3 |

**İniş durumu** (`landing_statuses`) — yalnızca `UAP` ve `UAİ` için; diğer sınıflarda `Inis Alani Degil` gönderin
| İsim | Değer |
|---|---|
| `Inilebilir` | "1" |
| `Inilemez` | "0" |
| `Inis Alani Degil` | "-1" |

**Hareket durumu** (`moving_statuses`) — yalnızca `Tasit` için; diğer sınıflarda `Tasit Degil` gönderin
| İsim | Değer |
|---|---|
| `Hareketli` | "1" |
| `Sabit` | "0" |
| `Tasit Degil` | "-1" |

---

## 7. Çalıştırma ve çıktılar

```shell
python main.py
```

Program çalışırken şu klasörleri oluşturur:

```
proje/
├── config/.env                 ← sizin giriş bilgileriniz
├── _logs/
│   └── <takım>_<tarih>.log      ← tüm işlemlerin kaydı (itirazlarda kullanılır)
└── _images/
    └── <oturum_adı>/
        ├── <kare>.webp          ← indirilen kareler
        ├── references.json      ← referans kataloğu
        └── references/          ← referans görüntüleri
            └── ref_1.png ...
```

> Kareler diske indiği için, program tekrar çalıştırıldığında daha önce inenleri yeniden indirmez. Bağlantı koparsa, tekrar `python main.py` deyince **kaldığı kareden** devam eder.

---

## 8. Sık karşılaşılan durumlar

| Durum | Anlamı / ne yapmalı |
|---|---|
| `No active session found. Exiting.` | Sunucuda aktif oturum yok. Yarışma/oturum başlamasını bekleyin. |
| `Could not reach the evaluation server...` | Sunucuya ulaşılamadı **veya** kullanıcı adı/şifre yanlış. `.env` ve internet bağlantınızı kontrol edin. (Detay için `_logs/` içindeki log dosyasına bakın.) |
| `All N frames already submitted.` | Bu oturumdaki tüm kareleri zaten gönderdiniz. Yapılacak bir şey yok. |
| `Session complete or no active session.` | Tüm kareler bitti, program normal şekilde sona erdi. |
| Bağlantı koptuysa | Tekrar `python main.py` çalıştırın; kaldığı kareden devam eder. |
| `Aborting: current frame is not advancing` | Tahmininiz sunucu tarafından sürekli reddediliyor (genelde hatalı veri). `_logs/` içindeki hatayı inceleyin. |

> **Kareler sıralıdır:** Sunucu, siz mevcut karenin tahminini göndermeden bir sonrakini vermez. Bu yüzden kareleri atlayamaz veya ileri saramazsınız.


Başarılar! 🚀🚀🚀
