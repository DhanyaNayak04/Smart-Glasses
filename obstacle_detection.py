import torch
import cv2
import numpy as np
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from image_capture import image_capture
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def estimate_depth_cpu(image_path="captured.jpg"):
    # Capture image using image_capture function
    image_path = image_capture()  # Should return the filename of the captured image

    # Load MiDaS model (DPT_Hybrid is lighter than DPT_Large)
    model_type = "DPT_Hybrid"  # You can also use "MiDaS_small" for even faster CPU inference

    midas = torch.hub.load("intel-isl/MiDaS", model_type)
    midas.eval()

    # Force CPU usage
    device = torch.device("cpu")
    midas.to(device)

    # Load appropriate transforms
    midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
    if model_type in ["DPT_Large", "DPT_Hybrid"]:
        transform = midas_transforms.dpt_transform
    else:
        transform = midas_transforms.small_transform

    # Load image and apply transform
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    input_batch = transform(img_rgb).to(device)

    # Run depth prediction
    with torch.no_grad():
        prediction = midas(input_batch)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()

    # Convert prediction to numpy array
    depth_map = prediction.cpu().numpy()

    # Normalize for display
    depth_min = depth_map.min()
    depth_max = depth_map.max()
    depth_vis = (255 * (depth_map - depth_min) / (depth_max - depth_min)).astype("uint8")

    # Apply color map
    depth_color = cv2.applyColorMap(depth_vis, cv2.COLORMAP_MAGMA)

    # Show results
    cv2.imshow("Original Image", img)
    cv2.imshow("Depth Map (CPU)", depth_color)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Detect potential close obstacles
    close_zone = depth_map < (depth_map.mean() * 0.6)
    if close_zone.any():
        print("⚠️ Obstacle detected nearby!")
    else:
        print("✅ No close obstacle detected.")

if __name__ == "__main__":
    estimate_depth_cpu()
