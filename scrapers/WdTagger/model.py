from io import BytesIO

import numpy as np
import onnxruntime as ort
import pandas as pd
from PIL import Image

from config import PREDICT_THRESHOLD, MODEL_PATH, TAG_PATH


class WD14Tagger:
    def __init__(self):
        self.model_file = MODEL_PATH
        self.tag_file = TAG_PATH
        self.threshold = PREDICT_THRESHOLD
        self.tags_df = None
        self.session = None

        self._load_model()

    def _load_model(self):
        # load tags
        self.tags_df = pd.read_csv(self.tag_file)

        self.session = ort.InferenceSession(
            path_or_bytes=self.model_file,
            providers=["CPUExecutionProvider"],  # "CUDAExecutionProvider"
        )

        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    @staticmethod
    def preprocess_image(image: Image.Image, target_size=448):
        """
        preprocess image:
        1. convert to RGB
        2. resize with aspect ratio and pad to 448x448
        3. normalize
        """
        # convert to RGB
        image = image.convert("RGB")

        # resize with aspect ratio
        w, h = image.size
        scale = min(target_size / w, target_size / h)
        new_w, new_h = int(w * scale), int(h * scale)
        image = image.resize((new_w, new_h), Image.BICUBIC)

        # create a white background square canvas
        new_img = Image.new("RGB", (target_size, target_size), (255, 255, 255))
        # paste the resized image to center
        new_img.paste(image, ((target_size - new_w) // 2, (target_size - new_h) // 2))
        img_array = np.array(new_img, dtype=np.float32)
        img_array = img_array[..., ::-1]

        img_array = np.expand_dims(img_array, axis=0)  # 增加 Batch 维度
        return img_array

    def get_rating(self, probs):
        # find the rating tag (category 9)
        ratings = self.tags_df[self.tags_df["category"] == 9]
        if ratings.empty:
            return "unknown"
        # assign probs
        max_idx = ratings["probs"].idxmax()
        return ratings.loc[max_idx, "name"]

    def predict(self, image_data: bytes) -> list[str]:
        image = Image.open(BytesIO(image_data))
        input_tensor = self.preprocess_image(image)

        # predict
        probs = self.session.run([self.output_name], {self.input_name: input_tensor})[0]

        # probs shape: (1, num_tags)
        probs = probs[0]

        # assign probs to tags_df
        self.tags_df["probs"] = probs

        # category 0 = general, 4 = character
        general_tags = self.tags_df[
            (self.tags_df["probs"] > self.threshold) & (self.tags_df["category"] == 0)
            ]

        character_tags = self.tags_df[
            (self.tags_df["probs"] > self.threshold) & (self.tags_df["category"] == 4)
            ]

        return character_tags["name"].tolist() + general_tags["name"].tolist() + [self.get_rating(probs)]
