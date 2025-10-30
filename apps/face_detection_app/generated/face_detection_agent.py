import cv2
from agent import Agent, Message
from camera_handler import CameraHandler

class FaceDetectionAgent(Agent):
    def __init__(self):
        super().__init__()
        self.camera = CameraHandler()

    def process_event(self, event):
        if event.type == 'FACE_DETECTION':
            self.handle_face_detection(event.data)

    def handle_face_detection(self, frame):
        # Get the current frame from the camera
        success, detected_frame = self.camera.get_frame()
        if success and detected_frame is not None:
            # Convert the frame to grayscale for face detection
            gray = cv2.cvtColor(detected_frame, cv2.COLOR_BGR2GRAY)
            # Detect faces in the grayscale frame
            faces = self.camera.detect_faces(gray)
            face_count = len(faces)
            face_coordinates = [(x, y, w, h) for (x, y, w, h) in faces]
            # Broadcast the detection results
            self.broadcast_detection(face_count, face_coordinates)
        else:
            # Handle the case where the frame could not be retrieved
            self.broadcast_detection(0, [])

    def broadcast_detection(self, face_count, face_coordinates):
        message = Message(
            type='FACE_DETECTION_RESULT',
            data={
                'count': face_count,
                'coordinates': face_coordinates
            }
        )
        self.send_message(message)

    def __del__(self):
        del self.camera