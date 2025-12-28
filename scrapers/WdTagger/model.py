from io import BytesIO
from pathlib import Path
from collections import defaultdict
import numpy as np
import onnxruntime as ort
import pandas as pd
from PIL import Image
from huggingface_hub import hf_hub_download
from config import MODEL, TAG, PREDICT_THRESHOLD

IMAGE_SIZE = 448


def load() -> tuple[ort.InferenceSession, pd.DataFrame]:
    # load model
    if MODEL:
        model_file = Path(MODEL) if Path(MODEL).is_file() else hf_hub_download(MODEL, "model.onnx")
    else:
        raise FileNotFoundError("Model file not found and huggingface_hub is not installed.")
    session = ort.InferenceSession(
        path_or_bytes=model_file,
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    # load tags
    if TAG:
        tag_file = Path(TAG) if Path(TAG).is_file() else hf_hub_download(TAG, "selected_tags.csv")
        tags_df = pd.read_csv(tag_file)
    else:
        raise FileNotFoundError("Tag file not found and huggingface_hub is not installed.")
    return session, tags_df


def preprocess(image: list[str | Path | bytes] | str | Path | bytes) -> np.ndarray:
    data = []
    if not isinstance(image, list):
        image = [image]
    for raw_img in image:
        if isinstance(raw_img, (str, Path)):
            img = Image.open(raw_img).convert("RGB")
        elif isinstance(raw_img, bytes):
            img = Image.open(BytesIO(raw_img)).convert("RGB")
        else:
            raise ValueError(f"Unsupported image type. {type(raw_img)}")
        # resize with aspect ratio
        w, h = img.size
        scale = min(IMAGE_SIZE / w, IMAGE_SIZE / h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.BICUBIC)
        # create a white background square canvas
        new_img = Image.new("RGB", (IMAGE_SIZE, IMAGE_SIZE), (255, 255, 255))
        # paste the resized image to center
        new_img.paste(img, ((IMAGE_SIZE - new_w) // 2, (IMAGE_SIZE - new_h) // 2))
        img_array = np.array(new_img, dtype=np.float32)
        img_array = img_array[..., ::-1]  # RGB -> BGR
        data.append(img_array)
    return np.stack(data)


def predict(
        session: ort.InferenceSession,
        tags_df: pd.DataFrame,
        images: list[str | Path | bytes] | str | Path | bytes
) -> list[tuple[str, float]]:
    input_name = session.get_inputs()[0].name
    label_name = session.get_outputs()[0].name

    imgs = preprocess(images)

    preds = session.run([label_name], {input_name: imgs})[0]

    results: list[tuple[str, float]] = []
    for i in range(len(images)):
        probs = preds[i]
        general_indices = np.where(probs > PREDICT_THRESHOLD)[0]
        res_tags = tags_df.iloc[general_indices]
        filtered_tags = res_tags[res_tags["category"] == 0]
        filtered_probs = probs[general_indices][res_tags["category"] == 0]
        tag_prob_pairs = list(zip(filtered_tags["name"], filtered_probs))
        results.extend(tag_prob_pairs)

    # 计算重复标签的概率均值
    tag_sum = defaultdict(float)
    tag_count = defaultdict(int)
    for tag, prob in results:
        tag_sum[tag] += prob
        tag_count[tag] += 1

    averaged_results = [(tag, tag_sum[tag] / tag_count[tag]) for tag in tag_sum]

    # 按概率降序排列
    averaged_results.sort(key=lambda x: x[1], reverse=True)

    return averaged_results
