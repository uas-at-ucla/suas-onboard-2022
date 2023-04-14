import torch
from torchvision import transforms
from torchvision.models import mobilenet_v3_large
import numpy as np

HIDDEN = 1280
POSSIBLE_TEXTS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
                  "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X",
                  "Y", "Z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
NUM_CLASSES = len(POSSIBLE_TEXTS)


class MobilenetWrapper:
    threshold = 0

    def __init__(self, path="/app/odlc/models/large_mobilent_6.pth"):
        self.net = mobilenet_v3_large()
        self.net.classifier[-1] = torch.nn.Linear(in_features=HIDDEN,
                                                  out_features=NUM_CLASSES,
                                                  bias=True)
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        if not torch.cuda.is_available():
            self.net.load_state_dict(torch.load(path, map_location="cpu"))
        else:
            self.net.load_state_dict(torch.load(path))

        self.net = self.net.to(self.device)

        self.net.eval()

        self.preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((120, 120)),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            )
        ])

    def decode_output(self, output) -> list:
        results = []
        for confidence, character in zip(output, POSSIBLE_TEXTS):
            if confidence > self.threshold:
                results.append((character, confidence))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def get_matching_text(self, image: np.ndarray) -> list:
        image = self.preprocess(image)
        image = image.to(self.device)

        image = image.reshape(1, 3, 120, 120)

        output = self.net(image)[0]
        return self.decode_output(output)
