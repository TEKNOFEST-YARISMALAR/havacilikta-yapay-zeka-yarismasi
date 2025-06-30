class Translation:
    def __init__(self,
                 translation_x: float,
                 translation_y: float,
                 translation_z: float,
                 ):

        self.translation_x = translation_x
        self.translation_y = translation_y
        self.translation_z = translation_z
    def create_payload(self):
        return {
                'translation_x': str(self.translation_x),
                'translation_y': str(self.translation_y),
                'translation_z': str(self.translation_z)
                }

    @staticmethod
    def generate_api_url(cls_endpoint, cls_id, evaulation_server):
        """
        Generates cls url for API usage
        """
        checked_url = evaulation_server if evaulation_server[-1] != "/" else evaulation_server + "/"
        return evaulation_server + cls_endpoint + cls_id + "/"
