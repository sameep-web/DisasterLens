import os
import numpy as np
import torch
import torch.nn as nn


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "best_landslide_unet_v5.pth"
)

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

INPUT_CHANNELS = 9
NUM_CLASSES = 2
IMAGE_SIZE = 128
THRESHOLD = 0.88


# ============================================================
# EXACT V5 CHANNELS
# ============================================================

SELECTED_CHANNELS = [
    0,
    1,
    2,
    3,
    4,
    10,
    11,
    12,
    13
]


# ============================================================
# EXACT V5 TRAINING MEAN
# ============================================================

TRAIN_MEAN = np.array([
    0.925704,
    0.922701,
    0.954109,
    0.959639,
    1.022790,
    1.042612,
    1.035844,
    1.046756,
    1.169941,
    1.173598,
    1.049497,
    1.037032,
    1.251108,
    1.649543
], dtype=np.float32)


# ============================================================
# EXACT V5 TRAINING STD
# ============================================================

TRAIN_STD = np.array([
    0.140988,
    0.220698,
    0.318425,
    0.572375,
    0.460096,
    0.446514,
    0.465075,
    0.494845,
    0.513311,
    0.683558,
    0.532293,
    0.662800,
    0.678369,
    1.072711
], dtype=np.float32)


# ============================================================
# DOUBLE CONV
# ============================================================

class DoubleConv(nn.Module):

    def __init__(
        self,
        in_channels,
        out_channels
    ):

        super().__init__()

        self.double_conv = nn.Sequential(

            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(
                out_channels
            ),

            nn.ReLU(
                inplace=True
            ),

            nn.Conv2d(
                out_channels,
                out_channels,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(
                out_channels
            ),

            nn.ReLU(
                inplace=True
            )
        )

    def forward(
        self,
        x
    ):

        return self.double_conv(
            x
        )


# ============================================================
# V5 U-NET
# ============================================================

class LandslideUNetV5(nn.Module):

    def __init__(
        self,
        in_channels=9,
        num_classes=2
    ):

        super().__init__()

        self.enc1 = DoubleConv(
            in_channels,
            32
        )

        self.enc2 = DoubleConv(
            32,
            64
        )

        self.enc3 = DoubleConv(
            64,
            128
        )

        self.enc4 = DoubleConv(
            128,
            256
        )

        self.pool = nn.MaxPool2d(
            2
        )

        self.bottleneck = DoubleConv(
            256,
            512
        )

        self.up4 = nn.ConvTranspose2d(
            512,
            256,
            2,
            stride=2
        )

        self.dec4 = DoubleConv(
            512,
            256
        )

        self.up3 = nn.ConvTranspose2d(
            256,
            128,
            2,
            stride=2
        )

        self.dec3 = DoubleConv(
            256,
            128
        )

        self.up2 = nn.ConvTranspose2d(
            128,
            64,
            2,
            stride=2
        )

        self.dec2 = DoubleConv(
            128,
            64
        )

        self.up1 = nn.ConvTranspose2d(
            64,
            32,
            2,
            stride=2
        )

        self.dec1 = DoubleConv(
            64,
            32
        )

        self.final = nn.Conv2d(
            32,
            num_classes,
            kernel_size=1
        )

    def forward(
        self,
        x
    ):

        e1 = self.enc1(x)

        e2 = self.enc2(
            self.pool(e1)
        )

        e3 = self.enc3(
            self.pool(e2)
        )

        e4 = self.enc4(
            self.pool(e3)
        )

        b = self.bottleneck(
            self.pool(e4)
        )

        d4 = self.up4(b)

        d4 = torch.cat(
            [d4, e4],
            dim=1
        )

        d4 = self.dec4(d4)

        d3 = self.up3(d4)

        d3 = torch.cat(
            [d3, e3],
            dim=1
        )

        d3 = self.dec3(d3)

        d2 = self.up2(d3)

        d2 = torch.cat(
            [d2, e2],
            dim=1
        )

        d2 = self.dec2(d2)

        d1 = self.up1(d2)

        d1 = torch.cat(
            [d1, e1],
            dim=1
        )

        d1 = self.dec1(d1)

        return self.final(
            d1
        )


# ============================================================
# LOAD MODEL
# ============================================================

print(
    "========================================"
)

print(
    "LOADING TERRAWATCH LANDSLIDE V5"
)

print(
    "========================================"
)


landslide_model = LandslideUNetV5(
    in_channels=INPUT_CHANNELS,
    num_classes=NUM_CLASSES
).to(
    DEVICE
)


if not os.path.exists(
    MODEL_PATH
):

    raise FileNotFoundError(
        "Checkpoint not found:\n"
        + MODEL_PATH
    )


checkpoint = torch.load(
    MODEL_PATH,
    map_location=DEVICE
)


if (
    isinstance(
        checkpoint,
        dict
    )
    and
    "model_state_dict"
    in checkpoint
):

    state_dict = (
        checkpoint[
            "model_state_dict"
        ]
    )

else:

    state_dict = checkpoint


landslide_model.load_state_dict(
    state_dict
)

landslide_model.eval()


print(
    "========================================"
)

print(
    "LANDSLIDE V5 MODEL LOADED SUCCESSFULLY"
)

print(
    "========================================"
)

print(
    "Checkpoint :",
    MODEL_PATH
)

print(
    "Device     :",
    DEVICE
)

print(
    "Input      :",
    INPUT_CHANNELS,
    "channels"
)

print(
    "Image size :",
    IMAGE_SIZE,
    "x",
    IMAGE_SIZE
)

print(
    "Classes    :",
    NUM_CLASSES
)

print(
    "Channels   :",
    SELECTED_CHANNELS
)

print(
    "Threshold  :",
    THRESHOLD
)

print(
    "========================================"
)


# ============================================================
# PREPROCESS
# ============================================================

def preprocess_live_image(
    image
):

    image = np.asarray(
        image,
        dtype=np.float32
    )

    if image.shape != (
        128,
        128,
        14
    ):

        raise ValueError(
            "Expected "
            "(128,128,14), got "
            + str(
                image.shape
            )
        )

    if not np.isfinite(
        image
    ).all():

        raise ValueError(
            "Live image contains NaN/Inf."
        )

    # HWC -> CHW
    tensor = torch.from_numpy(
        image
    ).permute(
        2,
        0,
        1
    )

    mean = torch.tensor(
        TRAIN_MEAN,
        dtype=torch.float32
    ).view(
        14,
        1,
        1
    )

    std = torch.tensor(
        TRAIN_STD,
        dtype=torch.float32
    ).view(
        14,
        1,
        1
    )

    # EXACT NOTEBOOK NORMALIZATION
    tensor = (
        tensor - mean
    ) / (
        std + 1e-8
    )

    # EXACT NOTEBOOK CHANNEL SELECTION
    tensor = tensor[
        SELECTED_CHANNELS,
        :,
        :
    ]

    tensor = tensor.unsqueeze(
        0
    )

    return tensor.to(
        DEVICE
    )


# ============================================================
# PREDICTION
# ============================================================

@torch.no_grad()
def predict_landslide(
    image
):

    input_tensor = (
        preprocess_live_image(
            image
        )
    )

    output = (
        landslide_model(
            input_tensor
        )
    )

    probabilities = (
        torch.softmax(
            output,
            dim=1
        )
    )

    landslide_probability = (
        probabilities[
            0,
            1
        ]
    )

    mask = (
        landslide_probability
        >= THRESHOLD
    )

    coverage = (
        mask
        .float()
        .mean()
        .item()
        * 100.0
    )

    return {

        "mask":
            mask
            .cpu()
            .numpy(),

        "probability":
            landslide_probability
            .cpu()
            .numpy(),

        "landslide_percentage":
            coverage
    }