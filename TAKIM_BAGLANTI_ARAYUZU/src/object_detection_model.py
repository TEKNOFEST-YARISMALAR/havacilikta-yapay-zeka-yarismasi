import logging
import time
import random
import requests

from .constants import classes, landing_statuses, moving_statuses
from .detected_object import DetectedObject
from .detected_translation import DetectedTranslation
from .reference_prediction import ReferencePrediction


class ObjectDetectionModel:
    # Base class for team models

    def __init__(self, evaluation_server_url):
        logging.info('Created Object Detection Model')
        self.evaulation_server = evaluation_server_url
        # Modelinizi bu kısımda init edebilirsiniz.
        # self.model = get_model() # Örnektir!

    @staticmethod
    def download_image(img_url, images_folder, images_files, retries=3, initial_wait_time=0.1, auth_token=None):
        t1 = time.perf_counter()
        wait_time = initial_wait_time
        # Indirmek istedigimiz frame frames.json dosyasinda mevcut mu kontrol edelim
        image_name = img_url.split("/")[-1]
        # Eger indirecegimiz frame'i daha once indirmediysek indirme islemine gecelim
        if image_name not in images_files:
            headers = {'Authorization': f'Token {auth_token}'} if auth_token else {}
            for attempt in range(retries):
                    try:
                        response = requests.get(img_url, headers=headers, timeout=60)
                        response.raise_for_status()
                        
                        img_bytes = response.content
                        with open(images_folder + image_name, 'wb') as img_file:
                            img_file.write(img_bytes)

                        t2 = time.perf_counter()
                        logging.info(f'{img_url} - Download Finished in {t2 - t1} seconds to {images_folder + image_name}')
                        return

                    except requests.exceptions.RequestException as e:
                        logging.error(f"Download failed for {img_url} on attempt {attempt + 1}: {e}")
                        logging.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        wait_time *= 2

            logging.error(f"Failed to download image from {img_url} after {retries} attempts.")
        # Eger indirecegimiz frame'i daha once indirdiysek indirme yapmadan devam edebiliriz
        else:
            logging.info(f'{image_name} already exists in {images_folder}, skipping download.')

    def process(self, prediction, evaluation_server_url, health_status, images_folder, images_files,
                active_refs=None, ref_image_paths=None, auth_token=None):
        # Yarışmacılar resim indirme, pre ve post process vb işlemlerini burada gerçekleştirebilir.
        # Download image (Ornek)
        self.download_image(evaluation_server_url + "media" + prediction.image_url, images_folder, images_files, auth_token=auth_token)
        # Örnek: Burada OpenCV gibi bir tool ile preprocessing işlemi yapılabilir. (Tercihe Bağlı)
        # ...
        # Nesne tespiti (Gorev 1), pozisyon kestirim (Gorev 2) ve referans nesne tespiti (Gorev 3)
        # modellerinin tumu self.detect() icinde sira ile calistirilir.
        frame_image_path = images_folder + prediction.image_url.split("/")[-1]
        frame_results = self.detect(prediction, health_status,
                                    active_refs=active_refs or [],
                                    ref_image_paths=ref_image_paths or {},
                                    frame_image_path=frame_image_path)
        # Tahminler objesi FramePrediction sınıfında return olarak dönülmelidir.
        return frame_results

    def detect(self, prediction, health_status, active_refs=None, ref_image_paths=None, frame_image_path=None):
        # Modelinizle bu fonksiyon içerisinde tahmin yapınız.
        # results = self.model.evaluate(...) # Örnektir.

        # Burada örnek olması amacıyla 2 adet tahmin yapıldığı simüle edilmiştir.
        # Yarışma esnasında modelin tahmin olarak ürettiği sonuçlar kullanılmalıdır.
        # Örneğin :
        # for i in results: # gibi
        for i in range(1, 3):
            cls = classes["UAP"],  # Tahmin edilen nesnenin sınıfı classes sözlüğü kullanılarak atanmalıdır.
            landing_status = landing_statuses["Inilebilir"]  # Tahmin edilen nesnenin inilebilir durumu landing_statuses sözlüğü kullanılarak atanmalıdır.
            # Moving status yalnizca Tasit (Vehicle) sinifi icin "Hareketli"/"Sabit" degerini alir.
            # UAP/UAI/Insan gibi tasit olmayan siniflar icin "Tasit Degil" ("-1") gonderilmelidir.
            moving_status = moving_statuses["Tasit Degil"] if int(cls[0]) != classes["Tasit"] else moving_statuses["Sabit"]
            top_left_x = 12 * i  # Örnek olması için rastgele değer atanmıştır. Modelin sonuçları kullanılmalıdır.
            top_left_y = 12 * i  # Örnek olması için rastgele değer atanmıştır. Modelin sonuçları kullanılmalıdır.
            bottom_right_x = 12 * i  # Örnek olması için rastgele değer atanmıştır. Modelin sonuçları kullanılmalıdır.
            bottom_right_y = 12 * i  # Örnek olması için rastgele değer atanmıştır. Modelin sonuçları kullanılmalıdır.

            # Modelin tespit ettiği herbir nesne için bir DetectedObject sınıfına ait nesne oluşturularak
            # tahmin modelinin sonuçları parametre olarak verilmelidir.
            d_obj = DetectedObject(cls,
                                   landing_status,
                                   moving_status,
                                   top_left_x,
                                   top_left_y,
                                   bottom_right_x,
                                   bottom_right_y
                                        )

            # Modelin tahmin ettiği her nesne prediction nesnesi içerisinde bulunan detected_objects listesine eklenmelidir.
            prediction.add_detected_object(d_obj)

        # Health Status biti hava aracinin uydu haberlesmesinin saglikli olup olmadigini gosterir.
        # Health Status 0 ise sistem calismali 1 ise gelen verinin aynisini gonderilebilir.
        # health_status None ise (ceviri sunucudan alinamadi) Gorev 2 ciktisi uretmeyiz; kare
        # yine de Gorev 1/3 ile gonderilip ilerletilir (bos detected_translations gecerlidir).
        if health_status is None:
            logging.info("No translation/health_status for this frame; skipping Mission 2 output.")
        elif health_status == '0':
            # Takimlar buraya kendi gelistirdikleri algoritmalarin sonuclarini entegre edebilirler.
            pred_translation_x = random.randint(1, 10) # Ornek olmasi icin rastgele degerler atanmistir takimlar kendi sonuclarini kullanmalidirlar.
            pred_translation_y = random.randint(1, 10) # Ornek olmasi icin rastgele degerler atanmistir takimlar kendi sonuclarini kullanmalidirlar.
            pred_translation_z = random.randint(1, 10) # Ornek olmasi icin rastgele degerler atanmistir takimlar kendi sonuclarini kullanmalidirlar.
            prediction.add_translation_object(
                DetectedTranslation(pred_translation_x, pred_translation_y, pred_translation_z))
        else:
            # Saglikli (health_status '1'): GT konum mevcut, oldugu gibi gonderilir. GT degerleri
            # null ise float'a cevrilemez (str(None) -> "None" sunucuda reddedilir); bu durumda atla.
            if None not in (prediction.gt_translation_x, prediction.gt_translation_y, prediction.gt_translation_z):
                prediction.add_translation_object(DetectedTranslation(
                    prediction.gt_translation_x, prediction.gt_translation_y, prediction.gt_translation_z))
            else:
                logging.info("Healthy frame but GT translation is null; skipping Mission 2 output.")

        # --- Gorev 3 (Referans Nesne Tespiti) ---
        # Gorev 1 ve Gorev 2'den sonra, ayni kare icin aktif olan her referans nesnesi
        # uzerinde sira ile calisir. `active_refs` ana donguden gelen pencere-ici aktif
        # referanslari tutar. Aralik disindaki kareler icin buraya hic aktif referans
        # iletilmez; dolayisi ile bu blok hicbir sey eklemez.
        for ref in (active_refs or []):
            start_img = ref.get('frame_start_image_url', '')
            end_img = ref.get('frame_end_image_url', '')
            if not (start_img and end_img and start_img <= prediction.image_url <= end_img):
                continue
            
            # Gorev 3 model cagrisi !
            # Ornek olmasi icin sabit bir bbox donuluyor. Takimlar kendi modellerini kullanmalidir.
            bbox = (10.0, 10.0, 120.0, 120.0)
            if not bbox:
                continue
            prediction.add_reference_prediction(
                ReferencePrediction(ref['url'], prediction.frame_url, *bbox)
            )

        return prediction
