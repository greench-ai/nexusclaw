# image-create — Image Generation Skill
> Supports ComfyUI (primary), AUTOMATIC1111, and Replicate.

## What This Skill Does

Generates images from text prompts via your configured image generation backend.
Default backend: ComfyUI at `COMFYUI_BASE_URL` (set in .env).

## Usage

```
Create an image of [description]
Generate [description] as an image
Draw [description]
```

## Supported Backends

| Backend | Env Var | Default URL |
|---------|---------|-------------|
| ComfyUI | `COMFYUI_BASE_URL` | `http://192.168.178.76:8188` |
| AUTOMATIC1111 | `AUTOMATIC1111_BASE_URL` | `http://localhost:7860` |
| Replicate | `REPLICATE_API_KEY` | cloud |

Backend priority: ComfyUI → AUTOMATIC1111 → Replicate

## Commands

| Command | Action |
|---------|--------|
| `Create an image of [prompt]` | Generate image with default settings |
| `Create a [size] image of [prompt]` | Specify size (512, 768, 1024, etc.) |
| `image-create status` | Check which backend is active |
| `image-create test` | Test connection to configured backend |

## ComfyUI Integration

For ComfyUI, the skill uses a default workflow JSON that:
- Loads a base SDXL or SD1.5 model (whichever is available)
- Uses standard txt2img pipeline
- Returns the generated image inline in chat

To use a custom workflow:
- Place it at `skills/image-create/workflows/custom.json`
- The skill will prefer it over the default

## Output

Generated images are:
1. Saved to `~/nexusclaw/library/images/YYYY-MM-DD/[timestamp].png`
2. Displayed inline in WebChat
3. Logged to `memory/artifacts/images.md`

## Config

`skills/image-create/config.json`:

```json
{
  "backend": "auto",
  "defaultSize": "1024x1024",
  "defaultSteps": 20,
  "saveImages": true,
  "comfyui": {
    "checkpointModel": "auto"
  }
}
```
