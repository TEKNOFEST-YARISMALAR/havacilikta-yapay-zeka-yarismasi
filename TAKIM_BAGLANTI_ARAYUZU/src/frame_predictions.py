class FramePredictions:
    def __init__(self, frame_url, image_url, video_name, gt_translation_x, gt_translation_y, gt_translation_z):
        self.frame_url = frame_url
        self.image_url = image_url
        self.video_name = video_name
        self.gt_translation_x = gt_translation_x
        self.gt_translation_y = gt_translation_y
        self.gt_translation_z = gt_translation_z
        self.translations = []
        self.detected_objects = []
        self.reference_predictions = []

    def add_detected_object(self, detection):
        self.detected_objects.append(detection)

    def add_translation_object(self, translation):
        self.translations.append(translation)

    def add_reference_prediction(self, ref_pred):
        self.reference_predictions.append(ref_pred)

    def create_detected_objects_payload(self, evaulation_server):
        payload = []
        for d_obj in self.detected_objects:
            sub_payload = d_obj.create_payload(evaulation_server)
            payload.append(sub_payload)
        return payload

    def create_translations_payload(self, evaulation_server):
        payload = []
        for d_obj in self.translations:
            sub_payload = d_obj.create_payload()
            payload.append(sub_payload)
        return payload

    def create_reference_predictions_payload(self):
        payload = []
        for rp in self.reference_predictions:
            sub_payload = rp.create_payload()
            payload.append(sub_payload)
        return payload

    def create_payload(self, evaulation_server):
        payload = {"frame": self.frame_url,
                   "detected_objects": self.create_detected_objects_payload(evaulation_server),
                   "detected_translations": self.create_translations_payload(evaulation_server),
                   "reference_predictions": self.create_reference_predictions_payload(),
                   }

        return payload
