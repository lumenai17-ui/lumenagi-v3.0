# Video Generation Research — SVD/FLUX Optimizations

## Current Stack
- **SVD:** /home/lumen/models/svd/ (local, moved to API soon)
- **FLUX:** API mode (no longer local VRAM)

## Optimization Opportunities

### 1. Batch Processing
- Process multiple frames in parallel
- Reduce API call overhead
- Cache intermediate results

### 2. Resolution Scaling
- Generate at 512x512, upscale with Real-ESRGAN
- 2-4x speed improvement
- Quality maintained with proper upscaling

### 3. Keyframe Sampling
- Generate every Nth frame
- Interpolate between keyframes
- Significant compute reduction

### 4. API Queue Management
- Priority queue for urgent generations
- Batch non-urgent requests
- Cost optimization via timing

## Implementation Status
- ⏳ Pending: Batch processor script
- ⏳ Pending: Upscale integration
- ⏳ Pending: Queue management system

## Next Steps
1. Create video_gen_batch.py for batch processing
2. Integrate with existing SVD location
3. Cost tracking per generation

---
*Research phase: 2026-02-11*
