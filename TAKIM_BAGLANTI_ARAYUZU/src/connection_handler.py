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
        self.video_name = ''
        self.img_save_path = './_images/'

        # URL'leri tanımla
        self.url_login = self.base_url + "auth/"
        self.url_frames = self.base_url + "frames/"
        self.url_translations = self.base_url + "translation/"
        self.url_prediction = self.base_url + "prediction/"
        self.url_session = self.base_url + "session/"
        self.url_reference = self.base_url + "reference/"
        self.url_progress = self.base_url + "progress/"

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

    def create_img_folder(self, path):
        post_path = os.path.join(self.img_save_path, path)
        os.makedirs(post_path, exist_ok=True)

    def get_listdir(self):
        save_path = os.path.join(self.img_save_path, self.video_name)
        return os.listdir(save_path), os.path.join(save_path)

    def get_progress(self, retries=3, initial_wait_time=0.5):
        """
        GET /progress/ — Returns the current user's position in the active session.

        Response dict:
            {
                "frame_index":  int   -- 0-based index of the next frame to predict
                "total_frames": int   -- total frames in the active session
                "completed":    bool  -- True when all frames have been predicted
                "session_name": str | None
            }
        """
        headers = {'Authorization': 'Token {}'.format(self.auth_token)}
        wait_time = initial_wait_time

        for attempt in range(retries):
            try:
                response = requests.get(self.url_progress, headers=headers, timeout=30)
                if response.status_code == 200:
                    progress = json.loads(response.text)
                    logging.info("Progress: frame {frame_index}/{total_frames} "
                                 "(completed={completed}, session={session_name})".format(**progress))
                    return progress
                else:
                    logging.error("Failed : get_progress : {}".format(response.text))
            except requests.exceptions.RequestException as e:
                logging.error(f"Progress request failed: {e}")

            logging.info(f"Retrying get_progress in {wait_time}s...")
            time.sleep(wait_time)
            wait_time *= 2

        # Sunucuya ulasilamadi. "Oturum yok" (session_name=None) ile karistirmamak icin
        # None doneriz; cagiran taraf bunu bir baglanti hatasi olarak ele almalidir.
        logging.error("get_progress failed after multiple retries.")
        return None

    def get_current_frame(self, retries=5, initial_wait_time=0.1):
        """
        GET /frames/ — Returns the single frame the user must predict next.

        The server now serves frames one at a time, gated by prediction submission.
        Calling this before sending a prediction returns the same frame again.

        Returns the frame dict, or None if the session is complete / inactive.

        Dikkat: Sunucu artık tüm frameleri birden dönmemektedir. Her çağrıda
        sıradaki tek kareyi döner. Tahmin gönderilmeden aynı kare tekrar gelir.
        """
        headers = {'Authorization': 'Token {}'.format(self.auth_token)}
        wait_time = initial_wait_time

        for attempt in range(retries):
            try:
                response = requests.get(self.url_frames, headers=headers, timeout=60)
                if response.status_code == 200:
                    frames = json.loads(response.text)
                    if not frames:
                        logging.info("get_current_frame: empty list (session complete or inactive).")
                        return None
                    frame = frames[0]
                    logging.info("get_current_frame: {}".format(frame.get('image_url')))
                    # Keep video_name in sync so get_listdir() and folder helpers work
                    if frame.get('video_name') and not self.video_name:
                        self.video_name = frame['video_name'] + '/'
                    return frame
                else:
                    logging.error("Failed : get_current_frame : {}".format(response.text))
            except requests.exceptions.RequestException as e:
                logging.error(f"get_current_frame request failed: {e}")

            logging.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2

        logging.error("get_current_frame failed after multiple retries.")
        return None

    def get_current_translation(self, retries=5, initial_wait_time=0.1):
        """
        GET /translation/ — Returns the translation record for the user's current frame.

        Mirrors the same gating as get_current_frame(): the server returns only
        the translation that corresponds to the frame the user has not yet predicted.

        Returns the translation dict, or None if unavailable.
        """
        headers = {'Authorization': 'Token {}'.format(self.auth_token)}
        wait_time = initial_wait_time

        for attempt in range(retries):
            try:
                response = requests.get(self.url_translations, headers=headers, timeout=60)
                if response.status_code == 200:
                    translations = json.loads(response.text)
                    if not translations:
                        logging.info("get_current_translation: empty list.")
                        return None
                    translation = translations[0]
                    logging.info("get_current_translation: {}".format(translation.get('image_url')))
                    return translation
                else:
                    logging.error("Failed : get_current_translation : {}".format(response.text))
            except requests.exceptions.RequestException as e:
                logging.error(f"get_current_translation request failed: {e}")

            logging.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2

        logging.error("get_current_translation failed after multiple retries.")
        return None

    def send_prediction(self, prediction, retries=5, initial_wait_time=0.1):
        """
        Dikkat: Sunucu tarafinda tahmin gonderimi icin dakikalik bir istek limiti vardir
        (limit sunucu tarafindan belirlenir ve yuksektir). main.py'deki MIN_FRAME_INTERVAL
        hizi bu limitin oldukca altinda tutar. Limit asilirsa sunucu gonderilen tahmini
        veritabanina yazmaz; bu yuzden hizi kontrol etmek yarismacilarin sorumlulugundadir.

        Limit asiminda sunucu HTTP 403 ile su bicimde bir cevap dondurur (mesaj degisebilir):
            {"detail":"Your requests has been exceeded <rate> limit."}
        (Eski surumlerde mesaj: {"detail":"You do not have permission to perform this action."})
        Yarismacilar bu gibi basarisiz bir gonderim icin tahmini tekrar gondermek uzere bir
        mekanizma tasarlayabilir.
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
                if response.status_code == 201:
                    logging.info("Prediction sent successfully. \n\t{}".format(payload))
                    return response
                elif response.status_code == 406:
                    logging.error(
                        "Prediction send failed - 406 Not Acceptable. Already sent. \n\t{}".format(response.text))
                    return response
                else:
                    logging.error("Prediction send failed. \n\t{}".format(response.text))
                    try:
                        detail = json.loads(response.text).get("detail", "")
                    except ValueError:
                        detail = ""
                    # Hiz limiti: yeni sunucu HTTP 403 + "...exceeded ... limit" doner; eski
                    # surumlerde mesaj "You do not have permission to perform this action." idi.
                    if (response.status_code == 403
                            or "exceeded" in detail.lower()
                            or "You do not have permission to perform this action." in detail):
                        logging.info("Rate limit hit. \n\t{}".format(response.text))
                        return response
            except requests.exceptions.RequestException as e:
                logging.error(f"Prediction request failed: {e}")

            logging.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2

        logging.error("Failed to send prediction after multiple retries.")
        return None


    def save_references_to_file(self, references):
        try:
            if not self.video_name:
                logging.warning("video_name not set; cannot cache references.json yet.")
                return
            refs_path = os.path.join(self.img_save_path, self.video_name, "references.json")
            with open(refs_path, 'w') as f:
                json.dump(references, f)
            logging.info(f"References saved to {refs_path}")
        except Exception as e:
            logging.warning(f"Failed to cache references: {e}")

    def load_references_from_file(self, session_name):
        base_path = os.path.join(self.img_save_path, session_name, "references.json")
        dirs = os.listdir(self.img_save_path) if os.path.exists(self.img_save_path) else []
        if session_name in dirs and os.path.exists(base_path):
            with open(base_path, 'r') as f:
                refs = json.load(f)
            logging.info(f"References loaded from {base_path}")
            return refs
        logging.warning(f"{base_path} does not exist.")
        return None

    def get_reference_objects(self, force_download=False, retries=5, initial_wait_time=0.1):
        """
        Dikkat: Bir dakika icerisinde bir takim maksimum 5 adet get_reference_objects istegi
        atabilmektedir. Bu kisit sunucuya gereksiz yuk binmesini engellemek icindir.

        Yeni Gorev 3 (Referans Nesne Tespiti) icin sunucudan yayinlanan referans nesneleri
        listesini doner. Her referans: {url, session, image_url, frame_start, frame_end, order}.
        """
        if not force_download:
            try:
                if os.path.exists(self.img_save_path) and self.video_name:
                    session_name = self.video_name.rstrip('/')
                    refs = self.load_references_from_file(session_name)
                    if refs:
                        logging.info("References file exists. Loading references from file.")
                        return refs
            except Exception:
                logging.info("References json exists, but it is corrupted.")

        headers = {'Authorization': 'Token {}'.format(self.auth_token)}
        wait_time = initial_wait_time

        for attempt in range(retries):
            try:
                response = requests.get(self.url_reference, headers=headers, timeout=60)
                if response.status_code == 200:
                    references = json.loads(response.text)
                    logging.info("Successful : get_reference_objects : {}".format(references))
                    self.save_references_to_file(references)
                    return references
                else:
                    logging.error("Failed : get_reference_objects : {}".format(response.text))
            except requests.exceptions.RequestException as e:
                logging.error(f"Get reference objects request failed: {e}")

            logging.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2

        logging.error("Failed to get reference objects after multiple retries.")
        return None
