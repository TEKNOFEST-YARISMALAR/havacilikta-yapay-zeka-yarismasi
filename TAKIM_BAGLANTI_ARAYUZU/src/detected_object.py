class DetectedObject:
    def __init__(self, cls: int,
                 landing_status: int,
                 moving_status: int,
                 top_left_x: float,
                 top_left_y: float,
                 bottom_right_x: float,
                 bottom_right_y: float,
                 ):

        self.cls = cls
        self.landing_status = str(landing_status)
        self.moving_status = str(moving_status)
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y
        self.bottom_right_x = bottom_right_x
        self.bottom_right_y = bottom_right_y

    def create_payload(self, evaulation_server):
        return {'cls': self.generate_api_url("classes/", str(int(self.cls[0]) + 1), evaulation_server),
                'landing_status': str(self.landing_status),
                'moving_status': str(self.moving_status),
                'top_left_x': str(self.top_left_x),
                'top_left_y': str(self.top_left_y),
                'bottom_right_x': str(self.bottom_right_x),
                'bottom_right_y': str(self.bottom_right_y)
                }

    @staticmethod
    def generate_api_url(cls_endpoint, cls_id, evaulation_server):
        """
        Generates cls url for API usage
        """
        checked_url = evaulation_server if evaulation_server[-1] != "/" else evaulation_server + "/"
        return evaulation_server + cls_endpoint + cls_id + "/"
