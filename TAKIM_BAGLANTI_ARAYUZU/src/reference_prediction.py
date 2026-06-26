class ReferencePrediction:
    """One reference-object detection submission for a single frame.

    Mirrors DetectedObject but targets Task 3 (Reference Object Detection):
    the server publishes reference objects (image + [frame_start, frame_end])
    and the team submits a bounding box per frame in that interval.
    """

    def __init__(self,
                 reference_url: str,
                 frame_url: str,
                 top_left_x: float,
                 top_left_y: float,
                 bottom_right_x: float,
                 bottom_right_y: float,
                 ):
        self.reference_url = reference_url
        self.frame_url = frame_url
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y
        self.bottom_right_x = bottom_right_x
        self.bottom_right_y = bottom_right_y

    def create_payload(self, evaulation_server=None):
        return {
            'reference': self.reference_url,
            'frame': self.frame_url,
            'top_left_x': str(self.top_left_x),
            'top_left_y': str(self.top_left_y),
            'bottom_right_x': str(self.bottom_right_x),
            'bottom_right_y': str(self.bottom_right_y),
        }
