# YOLO ROS / Standalone Detection

A concise guide for the YOLO-based detection project in this workspace. Contains ROS-friendly nodes and standalone scripts for running object detection on embedded and desktop platforms.

## Project Overview

- **Purpose:** Provide utilities and example nodes to run YOLO-based detection, publish images, and integrate with ROS and cloud services used for testing (Cloudinary / Firebase).
- **Key capabilities:** run detection models, publish detection results, sample image utilities, and launcher scripts for ROS and non-ROS usage.

## Repository Layout

- `src/bringup` — packaging and launch-related metadata for the bringup package.
- `src/main` — main package containing detection scripts, models, and helper utilities.
  - `src/main/main` — Python modules and runnable scripts (e.g. `main_with_ros.py`, `main_no_ros.py`, `simple_yolo_detect.py`, `image_publisher.py`).
  - `src/main/models` — model artifacts (`.pt`, `.onnx`, `.engine`).
  - `src/main/sample_images` — sample inputs to test detection.
  - `src/main/setup` — setup helper files and a local readme.

See the package manifests in `src/*/package.xml` for ROS packaging metadata.

## Quick Start

Requirements:
- Python 3.8+ (project uses Python 3.10 in some build artifacts).
- Typical Python packages: `numpy`, `opencv-python`, `torch` / `onnxruntime` / TensorRT bindings (depending on the model format), `Pillow`.

Recommended workflow (standalone, without ROS):

1. Install dependencies (create a `requirements.txt` if you want reproducible installs):

```bash
python3 -m pip install --user numpy opencv-python pillow
# add torch/onnxruntime/tensorrt as required for your model
```

2. Run the non-ROS demo:

```bash
python3 src/main/main/main_no_ros.py
```

ROS (colcon) workflow:

1. Build and source the workspace (colcon-based):

```bash
# from workspace root
colcon build
source install/setup.bash
```

2. Launch or run the relevant ROS node (see package manifests and node entry points in `src/main`).

## Models

Models are stored in `src/main/models`. The repository contains multiple formats (.pt, .onnx, .engine). Choose the runtime that matches your target platform.

## Testing & Samples

- Use images from `src/main/sample_images` to validate detection scripts.
- There are basic tests under `src/*/test` for packaging quality checks.

## Contributing

If you want to improve this README or add a requirements file, open a PR or ask for help. Suggested next steps:

- Add a `requirements.txt` or `pyproject.toml` with pinned dependencies.
- Add example launch files for ROS 2 (if you use ROS 2) and usage examples for each script.

## License

Add a `LICENSE` file to make the project license explicit. If none is provided, assume experimental/unlicensed.

---
For package-specific details see `src/main/setup/readme.md`.
