from build_my_startup import Agent
import openai

class CommentaryAgent(Agent):
    def __init__(self, api_key, style):
        """Initialize the CommentaryAgent with API key and style."""
        super().__init__()
        openai.api_key = api_key
        self.style = style

    def generate_commentary(self, image_data):
        """Generate commentary for the given image data."""
        response = openai.Image.create(
            file=image_data,
            model="vision",
            prompt=f"Generate commentary in the style of {self.style}."
        )
        # Assuming the response structure contains 'data' with 'commentary'
        return response['data']['commentary']

    def handle_image_upload(self, image_data):
        """Handle the image upload and generate commentary."""
        commentary = self.generate_commentary(image_data)
        return commentary