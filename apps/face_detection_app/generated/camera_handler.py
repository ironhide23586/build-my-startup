import cv2

class CameraHandler:
    def __init__(self):
        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            raise Exception("Could not open video device")
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def get_frame(self):
        success, frame = self.video_capture.read()
        if not success:
            return False, None  # Return None if frame read fails
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detect_faces(gray)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        return True, frame  # Indicate success and return the frame

    def detect_faces(self, gray_frame):
        return self.face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5)

    def __del__(self):
        if self.video_capture.isOpened():
            self.video_capture.release()
        cv2.destroyAllWindows()