import json
import logging
import requests
import time
import os
from decouple import config


class ConnectionHandler:
    def __init__(self, base_url, username=None, password=None):
        self.base_url = base_url
        self.auth_token = None
        self.classes = None
        self.frames = None
        self.translations = None
        self.frames_file = "frames.json"  # Kaydedilen frames dosyası
        self.translations_file = "translations.json"  # Kaydedilen translations dosyası
        self.video_name = ''
        self.img_save_path = './_images/'
        

        # URL'leri tanımla
        self.url_login = self.base_url + "auth/"
        self.url_frames = self.base_url + "frames/"
        self.url_translations = self.base_url + "translation/"
        self.url_prediction = self.base_url + "prediction/"
        self.url_session = self.base_url + "session/"

        if username and password:
            self.login(username, password)

    def login(self, username, password):
        payload = {'username': username, 'password': password}
        files = []
        try:
            response = requests.post(self.url_login, data=payload, files=files, timeout=10)
            response_json = json.loads(response.text)
            if response.status_code == 200:
                self.auth_token = response_json['token']
                logging.info("Login Successfully Completed : {}".format(payload))
            else:
                logging.error("Login Failed : {}".format(response.text))
        except requests.exceptions.RequestException as e:
            logging.error(f"Login request failed: {e}")           


    def write_to_env(self, session_name=None):
        found = False
        change = False
        # iterates over the lines, enters the condition on session_name line
        with open("./config/.env", "r+") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                # line check
                if line.startswith("SESSION_NAME="):
                    if session_name == line.split("=")[-1].strip():
                        found = True
                        logging.info(f"{session_name} json exists, returning..")
                        return line.split("=")[-1].strip()
                    else:
                        # exists but different
                        lines[i] = f"SESSION_NAME={session_name}\n"
                        change = True

            if change:
                f.seek(0)
                f.writelines(lines)
                f.truncate()
                logging.info(f"Changed the session to {session_name}")
                return session_name       

            if not found:
                # case1, no session_name
                lines.append(f"\nSESSION_NAME={session_name}\n")
                f.seek(0)
                f.writelines(lines)
                f.truncate()
                logging.info(f"Entered the session of {session_name}")
            
            return session_name

    def get_session_name(self):
        # Config dosyasi icinde tanimlanmis olan oturum ismini cekelim.
        # Oturum ismi config dosyasi icinde tanimlanmamissa sunucuya istek atarak cekilir.
        config.search_path = "../config/"
        return config("SESSION_NAME")

    def create_img_folder(self, path):
        post_path = os.path.join(self.img_save_path, path)
        os.makedirs(post_path, exist_ok=True)        
    
    def get_listdir(self):
        save_path = os.path.join(self.img_save_path, self.video_name)
        return os.listdir(save_path), os.path.join(save_path)

    def save_frames_to_file(self, frames):
        try:
            self.video_name = frames[0]['video_name'] + '/'
            # create the dir
            self.create_img_folder(self.video_name)
            # update the dir
            self.write_to_env(frames[0]['video_name'])
            
            frames_path = os.path.join(self.img_save_path, self.video_name, self.frames_file)
            
            with open(frames_path, 'w') as f:
                json.dump(frames, f)
            logging.info(f"Frames saved to {frames_path}")
        except IndexError as e:
            logging.error(f"{e} has occured!")
            raise 
        
    def load_frames_from_file(self, session_name):
        # Indirilen frameleri tekrardan indirmeyerek dogrudan klasorden okumamizi saglayan fonksiyondur.
        # Ornek: "_images/Test_Oturumu" gibi isimli yolumuzdan frameleri yukleyelim
        base_path = os.path.join(self.img_save_path, session_name, self.frames_file)
        dirs = os.listdir(self.img_save_path)
        if session_name in dirs:
            if os.path.exists(base_path):
                with open(base_path, 'r') as f:
                    frames = json.load(f)
                logging.info(f"Frames loaded from {base_path}")
                return frames
        logging.warning(f"{base_path} does not exist.")
        return None
    
    def get_frames(self, force_download=False, retries=5, initial_wait_time=0.1):
        """
        Dikkat: Bir dakika içerisinde bir takım maksimum 5 adet get_frames isteği atabilmektedir.
        Bu kısıt yarışma esnasında yarışmacıların gereksiz istek atarak sunucuya yük binmesini
        engellemek için tanımlanmıştır. get_frames fonksiyonunu kullanırken bu kısıtı göz önünde
        bulundurmak yarışmacıların sorumluluğundadır.
        """
        if not force_download:
            try:
                # _images klasorunun mevcut olup olmadigini kontrol edelim
                if os.path.exists(self.img_save_path):
                    # Eger _images klasoru olusturulmussa oturum ismimizi cekelim
                    session_name = self.get_session_name()
                    # Daha onceden indirilmis frameler var ise dosyadan o frameler yukleyelim.
                    frames = self.load_frames_from_file(session_name)
                    # framelerin oldugu dosyanin bos olmamasi durumunda
                    if frames:
                        self.video_name = session_name + "/"
                        logging.info("Frames file exists. Loading frames from file.")
                        return frames
            except:
                logging.info("Frames file exists, but it is corrupted.")

            
        payload = {}
        headers = {'Authorization': 'Token {}'.format(self.auth_token)}
        wait_time = initial_wait_time

        # Fonksiyonumuzu arka arkaya uc deneme yapacak sekilde ayarlayalim
        for attempt in range(retries):
            try:
                # Framelerin dosya yolunu cekebilmek icin sunucuya get istegi atalim.
                # Burada timeout degeri 60 saniye olarak belirlenmistir.
                response = requests.get(self.url_frames, headers=headers, data=payload, timeout=60)
                self.frames = json.loads(response.text)
                # Get istegi basarili bir sekilde donduyse frameleri ilgili klasore kaydedelim
                if response.status_code == 200:
                    logging.info("Successful : get_frames : {}".format(self.frames))
                    self.save_frames_to_file(self.frames)
                    return self.frames
                else:
                    # Aksi durumda fail durumunu loglayalim
                    logging.error("Failed : get_frames : {}".format(response.text))
            except requests.exceptions.RequestException as e:
                logging.error(f"Get frames request failed: {e}")

            # Denememizde basari saglayamadiysak kisa bir sure bekleyip tekradan istegimizi sunucuya gonderelim.
            logging.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2

        logging.error("Failed to get frames after multiple retries. Loading frames from file.")
        return self.load_frames_from_file(session_name)


    def save_translations_to_file(self, translations):
        try:
            translations_path = os.path.join(self.img_save_path, self.video_name, self.translations_file)
                                   
            with open(translations_path, 'w') as f:
                json.dump(translations, f)
                
            logging.info(f"Translations saved to {translations_path}")
        except:
            logging.warning("An error has occured")
            
    def load_translations_from_file(self, session_name):
        # e.g. "_images/2024_tuyz_xxx/"
        base_path = os.path.join(self.img_save_path, session_name, self.translations_file)
        dirs = os.listdir(self.img_save_path)
        if session_name in dirs:
            if os.path.exists(base_path):
                with open(base_path, 'r') as f:
                    translations = json.load(f)
                logging.info(f"Translations loaded from {base_path}")
                return translations
        logging.warning(f"{base_path} does not exist.")
        return None

    def get_translations(self, force_download=False, retries=5, initial_wait_time=0.1):
        """
          Dikkat: Bir dakika içerisinde bir takım maksimum 5 adet get_frames isteği atabilmektedir.
          Bu kısıt yarışma esnasında yarışmacıların gereksiz istek atarak sunucuya yük binmesini
          engellemek için tanımlanmıştır. get_frames fonksiyonunu kullanırken bu kısıtı göz önünde
          bulundurmak yarışmacıların sorumluluğundadır.
          """
        if not force_download:
            try:
                # _images klasorunun mevcut olup olmadigini kontrol edelim
                if os.path.exists(self.img_save_path):
                    # Eger _images klasoru olusturulmussa oturum ismimizi cekelim
                    session_name = self.get_session_name()
                    # Daha onceden indirilmis translations var ise dosyadan o frameler yukleyelim.
                    translations = self.load_translations_from_file(session_name)
                    # translationlarin oldugu dosyanin bos olmamasi durumunda
                    if translations:
                        logging.info("Translations file exists. Loading translations from file.")
                        return translations
            except:
                logging.info("Translation json exists, but it is corrupted.")
        
        payload = {}
        headers = {'Authorization': 'Token {}'.format(self.auth_token)}
        wait_time = initial_wait_time

        for attempt in range(retries):
            try:
                # Framelerin dosya yolunu cekebilmek icin sunucuya get istegi atalim.
                # Burada timeout degeri 60 saniye olarak belirlenmistir.
                response = requests.get(self.url_translations, headers=headers, data=payload, timeout=60)
                self.translations = json.loads(response.text)
                # Get istegi basarili bir sekilde donduyse translationlari ilgili klasore kaydedelim
                if response.status_code == 200:
                    logging.info("Successful : get_translations : {}".format(self.translations))
                    self.save_translations_to_file(self.translations)
                    return self.translations
                else:
                    # Aksi durumda fail durumunu loglayalim
                    logging.error("Failed : get_translations : {}".format(response.text))
            except requests.exceptions.RequestException as e:
                logging.error(f"Get translations request failed: {e}")

            # Denememizde basari saglayamadiysak kisa bir sure bekleyip tekradan istegimizi sunucuya gonderelim.
            logging.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2

        logging.error("Failed to get translations after multiple retries. Loading translations from file.")
        return self.load_translations_from_file(session_name)

    def send_prediction(self, prediction, retries=5, initial_wait_time=0.1):
        """
        Dikkat: Bir dakika içerisinde bir takım maksimum 80 frame için tahmin gönderebilecektir.
        Bu kısıt yarışma esnasında yarışmacıların gereksiz istek atarak sunucuya yük binmesini
        engellemek için tanımlanmıştır. send_prediction fonksiyonunu kullanırken bu kısıtı göz
        önünde bulundurmak yarışmacıların sorumluluğundadır.

        Öneri: Bir dakika içerisinde gönderilen istek sayısı tutularak sistem hızlı çalışıyorsa
        bekletilebilir (wait() vb). Azami istek sınırı aşıldığında sunucu gönderilen tahmini
        veritabanına yazmamaktadır. Dolayısı ile bu durumu gözardı eden takımların istek sınır
        aşımı yapan gönderimleri değerlendirilMEyecektir. İstek sınırı aşıldığında sunucu aşağıdaki
        cevabı dönmektedir:
            {"detail":"You do not have permission to perform this action."}
        Ayrıca yarışmacılar sunucudan bu gibi başarısız bir gönderimi işaret eden cevap alındığında
        gönderilemeyen tahmini sunucuya tekrar göndermek üzere bir mekanizma tasarlayabilir.
        """


        payload = json.dumps(prediction.create_payload(self.base_url))
        files = []
        headers = {
            'Authorization': 'Token {}'.format(self.auth_token),
            'Content-Type': 'application/json',
        }
        wait_time = initial_wait_time

        for attempt in range(retries):
            try:
                response = requests.post(self.url_prediction, headers=headers, data=payload, files=files, timeout=60)
                # Ilgili frame icin basarili sekilde tahmin gonderebildiysek
                if response.status_code == 201:
                    logging.info("Prediction sent successfully. \n\t{}".format(payload))
                    return response
                # Ilgili frame'e ait olan tahmimizi daha once gondermis oldugumuz icin gonderemediysek loglayalim ve
                # donguden cikalim. Aynı frame icin tekrar tekrar tahmin atmayi denemeyelim
                elif response.status_code == 406:
                    logging.error(
                        "Prediction send failed - 406 Not Acceptable. Already sent. \n\t{}".format(response.text))
                    return response
                # Hali hazirda gondermis olmamiz disinda bir sebepten tahmin gonderemiyorsak loglama yapalim
                else:
                    logging.error("Prediction send failed. \n\t{}".format(response.text))
                    response_json = json.loads(response.text)
                    if "You do not have permission to perform this action." in response_json.get("detail", ""):
                        logging.info("Limit exceeded. 80frames/min \n\t{}".format(response.text))
                        return response
            except requests.exceptions.RequestException as e:
                logging.error(f"Prediction request failed: {e}")

            # Belli bir sure bekleyip ilgili frame icin tahmin gondermeyi tekrar deneyelim
            logging.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2

        logging.error("Failed to send prediction after multiple retries.")
        return None

