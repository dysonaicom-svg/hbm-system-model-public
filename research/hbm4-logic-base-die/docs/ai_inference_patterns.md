# AI Inference Patterns for HBM4 Logic-Based Die Architecture

## 1. Overview

This document catalogs inference-specific architectural patterns, serving strategies, and optimization techniques for AI/ML inference workloads on HBM4-based systems with logic-based dies. While training patterns focus on throughput and gradient computation, inference patterns emphasize latency, memory efficiency, and dynamic batching.

## 2. Inference vs. Training Memory Profiles

### 2.1 Memory Footprint Comparison

```
Workload Phase      │ Active Memory    │ Access Pattern │ HBM4 Optimization
────────────────────┼──────────────────┼────────────────┼───────────────────
Training (forward)  │ activations      │ write-heavy     │ Channel striping
Training (backward) │ activations+grad │ read/write mix │ Pipeline buffering
Inference (prefill)  │ activations+KV   │ write-heavy     │ Sequential writes
Inference (decode)   │ KV cache read    │ read-heavy      │ Streaming reads
```

### 2.2 Key Differences in HBM4 Utilization

| Aspect | Training | Inference |
|--------|----------|-----------|
| Memory Write Ratio | 60-70% | 20-30% |
| Sequential Access | Mixed | Prefill: sequential, Decode: random |
| Batch Size | Large (tens-hundreds) | Small (1-16) |
| KV Cache | N/A | 70-90% of memory |
| Model Weights | Static + gradients | Read-only |
| Latency Constraint | Throughput | P99 latency |

## 3. Inference Architecture Patterns

### 3.1 Streaming Decode Pattern

```
┌────────────────────────────────────────────────────────────────────────┐
│                    HBM4 Inference Pipeline                          │
│                                                                    │
│  Prefill Phase:                                                    │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│  │ Token 0  │ → │ Token 1  │ → │ Token 2  │ → │  ... N   │        │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘        │
│       │               │               │               │              │
│       └───────────────┴───────────────┴───────────────┘              │
│                               │                                     │
│                               ↓                                     │
│                    ┌─────────────────────┐                          │
│                    │   KV Cache Write    │                          │
│                    │  (Sequential Burst) │                          │
│                    └──────────┬──────────┘                          │
│                               │                                     │
│                               ↓                                     │
│  Decode Phase (Token-by-Token):                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│  │ KV Read  │ → │ Compute │ → │ Gen Token│ → │ KV Write │        │
│  │ (Random) │   │         │   │          │   │(Sequential)│        │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘        │
│                                                                    │
│  HBM4 Optimization:                                                │
│  - Prefill: Use all 32 channels, high BW                          │
│  - Decode: Channel striping for KV cache to hide latency           │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 KV Cache Management Patterns

```python
class KVCacheManager:
    """
    Manages KV cache placement across 32 HBM4 channels for inference.
    
    Key optimizations:
    - KV cache typically consumes 70-90% of inference memory
    - Attention patterns favor sequential reads during decode
    - Channel striping reduces per-token latency
    """
    
    def __init__(self, num_channels=32):
        self.num_channels = num_channels
        self.cache_layouts = {
            "layer_parallel": {},  # Layers distributed across channels
            "head_parallel": {},   # Attention heads distributed
            "channel_stripe": {}    # Full KV block striped
        }
    
    def allocate_cache(self, num_layers, num_heads, seq_len, head_dim):
        """
        Allocate KV cache with HBM4-optimal layout.
        
        Args:
            num_layers: Number of transformer layers
            num_heads: Number of attention heads per layer
            seq_len: Maximum sequence length
            head_dim: Dimension per attention head
            
        Returns:
            Channel allocation map for KV cache
        """
        cache_per_layer = 2 * num_heads * seq_len * head_dim * 2  # K + V, BF16
        
        # Strategy: Stripe KV across all channels for minimal decode latency
        chunk_per_channel = cache_per_layer // self.num_channels
        
        allocation = {}
        for ch in range(self.num_channels):
            allocation[ch] = {
                "layers": [],  # Layers stored on this channel
                "size_bytes": chunk_per_channel
            }
        
        # Distribute layers across channels
        for layer_idx in range(num_layers):
            ch = layer_idx % self.num_channels
            allocation[ch]["layers"].append(layer_idx)
        
        return allocation
    
    def optimize_for_decode(self, access_pattern):
        """
        Optimize KV cache layout based on decode access patterns.
        
        Decode access is per-layer, per-head, sequential in position.
        Layout should minimize bank conflicts during attention computation.
        """
        # Interleave at position granularity for better bank utilization
        # Position N on channel (N % 32), enabling parallel attention
        pass
```

## 4. Serving Patterns

### 4.1 Continuous Batching with HBM4

```python
class HBM4ContinuousBatcher:
    """
    Continuous batching optimized for HBM4 memory bandwidth.
    
    Key insight: HBM4's 512GB/s aggregate bandwidth enables
    efficient processing of small batches when properly scheduled.
    """
    
    def __init__(self, model, hbm4_channels):
        self.model = model
        self.channels = hbm4_channels  # 32 channels
        self.max_batch_size = self._calculate_optimal_batch()
    
    def _calculate_optimal_batch(self):
        """
        Calculate batch size that maximizes HBM4 bandwidth utilization.
        
        HBM4 provides ~16GB/s per channel, ~512GB/s total.
        For BF16 compute, aim for > 50% BW utilization.
        """
        # Per-token KV cache: ~16 bytes (K: 2*seq*head_dim*2)
        # Plus activations, weights already loaded
        kv_cache_per_token = 16 * 1024  # ~16KB per token in cache
        
        # Available memory per channel: 16GB
        # Reserve 20% for activations, activations
        usable_per_channel = 16 * 0.8 * (1024**3)
        
        # Max tokens in KV cache
        max_tokens = usable_per_channel // kv_cache_per_token
        
        # Optimal batch balances memory and compute
        return min(int(max_tokens * 0.7), 64)  # Conservative margin
    
    def schedule_batch(self, pending_requests):
        """
        Schedule requests into batches optimizing HBM4 utilization.
        
        Strategy:
        1. Group by sequence length (minimize padding)
        2. Interleave sequences across channels for parallel prefetch
        3. Prioritize requests with common prefixes (KV cache sharing)
        """
        # Sort by sequence length for memory efficiency
        sorted_requests = sorted(pending_requests, 
                                  key=lambda r: r.seq_len)
        
        batches = []
        current_batch = []
        current_tokens = 0
        
        for req in sorted_requests:
            if current_tokens + req.seq_len > self.max_batch_size:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [req]
                current_tokens = req.seq_len
            else:
                current_batch.append(req)
                current_tokens += req.seq_len
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
```

### 4.2 Prefix Caching Pattern

```
┌────────────────────────────────────────────────────────────────────────┐
│                    Prefix Cache Architecture                           │
│                                                                    │
│  Request 1: "What is the capital of [France]?"                      │
│  Request 2: "What is the capital of [Germany]?"                     │
│  Request 3: "What is the capital of [Italy]?"                       │
│                                                                    │
│  System Prompt: "You are a helpful assistant."                      │
│  Common Prefix: ┌─────────────────────────┐                          │
│                 │ KV cache sharable      │ ← Cache on HBM4           │
│                 └─────────────────────────┘                          │
│                 ↓                                                    │
│  Variable Part: ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│                 │ [France] │ │[Germany] │ │ [Italy]  │            │
│                 └──────────┘ └──────────┘ └──────────┘            │
│                                                                    │
│  HBM4 Optimization:                                                │
│  - Reserve 25% of channels for persistent prefix cache              │
│  - Use content-addressable lookup for prefix matching               │
│  - Batch requests with shared prefixes                              │
└────────────────────────────────────────────────────────────────────┘
```

### 4.3 Speculative Decoding Pattern

```python
class SpeculativeDecodingScheduler:
    """
    Speculative decoding with HBM4-optimized draft/execute coordination.
    
    Draft model runs faster but lower quality.
    Target model verifies drafts in parallel.
    HBM4 BW enables efficient draft verification.
    """
    
    def __init__(self, draft_model, target_model, hbm4_channels):
        self.draft = draft_model
        self.target = target_model
        self.channels = hbm4_channels
        self.draft_kv_channels = 16  # Half channels for draft
        self.target_kv_channels = 16  # Half channels for target
    
    def schedule_speculative_batch(self, kv_cache_state, num_spec_tokens=4):
        """
        Schedule speculative decode batch across HBM4 channels.
        
        Channel allocation:
        - 16 channels: Draft model KV cache (faster, smaller model)
        - 16 channels: Target model KV cache (verification)
        
        HBM4 BW enables parallel draft generation and target verification.
        """
        # Draft phase: Generate speculative tokens
        draft_input = self.prepare_draft_input(kv_cache_state)
        draft_tokens = self.draft.forward(draft_input, 
                                        channel_slice=self.draft_kv_channels)
        
        # Target verification: Check all drafts in parallel
        for token_idx in range(num_spec_tokens):
            target_verify = self.target.verify_single(
                draft_tokens[token_idx],
                channel_slice=self.target_kv_channels
            )
            
            if not target_verify.accept:
                # Revert to target's preferred token
                self.rollback_kv_cache(token_idx)
                break
        
        return self.format_response(draft_tokens, target_verify)
```

## 5. Quantization Patterns for Inference

### 5.1 Weight-Only Quantization

```python
class HBM4WeightQuantizer:
    """
    Weight-only quantization optimized for HBM4 inference.
    
    Key insight: Weights are read-only during inference,
    enabling aggressive quantization without training overhead.
    """
    
    QUANTIZATION_CONFIGS = {
        "INT8": {
            "bits": 8,
            "memory_reduction": 2.0,  # 2x reduction
            "accuracy_impact": "< 1% degradation typical",
            "hbm4_benefit": "2x effective bandwidth"
        },
        "INT4": {
            "bits": 4,
            "memory_reduction": 4.0,  # 4x reduction
            "accuracy_impact": "1-5% degradation (model dependent)",
            "hbm4_benefit": "4x effective bandwidth"
        },
        "FP8_E4M3": {
            "bits": 8,
            "memory_reduction": 2.0,
            "accuracy_impact": "~0.5% degradation typical",
            "hbm4_benefit": "Mixed precision, good for activations"
        },
        "FP8_E5M2": {
            "bits": 8,
            "memory_reduction": 2.0,
            "accuracy_impact": "Similar to BF16 for most models",
            "hbm4_benefit": "Better for gradients during prefilled"
        }
    }
    
    def quantize_weights(self, weights, quantization_type="INT8"):
        """
        Quantize model weights for inference.
        
        HBM4 channel striping works with quantized weights
        without modification - just smaller data per channel.
        """
        config = self.QUANTIZATION_CONFIGS[quantization_type]
        
        # Per-channel quantization for better accuracy
        num_channels = 32
        chunk_size = len(weights) // num_channels
        
        quantized = []
        for ch in range(num_channels):
            chunk = weights[ch*chunk_size:(ch+1)*chunk_size]
            # Per-channel calibration
            scale = chunk.abs().max() / (2**(config["bits"] - 1))
            quantized_chunk = (chunk / scale).round().to(torch.int8)
            quantized.append({
                "data": quantized_chunk,
                "scale": scale,
                "channel": ch
            })
        
        return quantized
    
    def plan_memory_layout(self, model_size, quantization):
        """
        Plan HBM4 memory layout for quantized weights.
        
        Smaller weights enable:
        - More layers in HBM4 cache
        - Larger KV cache
        - More batches in flight
        """
        config = self.QUANTIZATION_CONFIGS[quantization]
        quantized_size = model_size / config["memory_reduction"]
        
        # Channels needed for weights
        weight_channels = int(np.ceil(quantized_size / (16 * 1024**3)))
        
        # Remaining channels for KV cache and activations
        kv_cache_channels = 32 - weight_channels
        
        return {
            "weight_channels": weight_channels,
            "kv_cache_channels": kv_cache_channels,
            "effective_bw_multiplier": config["memory_reduction"]
        }
```

### 5.2 KV Cache Quantization

```python
class KVCacheQuantizer:
    """
    KV cache quantization for extended sequence lengths.
    
    Key insight: KV cache accessed sequentially during decode,
    enabling INT4 quantization with minimal latency impact.
    """
    
    def __init__(self, num_channels=32):
        self.num_channels = num_channels
        self.kv_quantization_ratio = 0.5  # INT4 = 50% of INT8 size
    
    def quantize_kv_cache(self, kv_tensor, precision="INT8"):
        """
        Quantize KV cache tensor.
        
        Layout preserved - just smaller per-element storage.
        Channel striping unaffected.
        """
        if precision == "INT8":
            scale = kv_tensor.abs().max() / 127.0
            return (kv_tensor / scale).to(torch.int8), scale
        elif precision == "INT4":
            # Packed INT4 storage
            packed = self.pack_int4(kv_tensor)
            scale = kv_tensor.abs().max() / 7.0
            return packed, scale
    
    def pack_int4(self, tensor):
        """
        Pack INT4 values for 50% storage reduction.
        
        Two INT4 values per byte.
        Requires careful handling for HBM4 channel boundaries.
        """
        # Round up to even number of elements
        padded_len = (len(tensor) + 1) // 2 * 2
        padded = F.pad(tensor, (0, padded_len - len(tensor)))
        
        # Pack pairs of INT4 values
        high_nibbles = (padded[0::2] & 0x0F).to(torch.uint8)
        low_nibbles = (padded[1::2] & 0x0F).to(torch.uint8)
        
        packed = (low_nibbles << 4) | high_nibbles
        
        # Channel boundary alignment for HBM4
        # Each channel should start on even byte boundary
        return packed
```

## 6. Latency-Critical Patterns

### 6.1 P99 Latency Optimization

```python
class P99LatencyOptimizer:
    """
    Optimizations specifically targeting P99 latency.
    
    Key metrics:
    - Time to First Token (TTFT): Prefill performance
    - Time per Output Token (TPOT): Decode performance
    - Total latency = TTFT + (num_tokens × TPOT)
    """
    
    def __init__(self, hbm4_config):
        self.channels = hbm4_config["num_channels"]
        self.burst_size = hbm4_config["burst_size"]  # 256B typical
    
    def optimize_ttft(self, input_tokens):
        """
        Optimize Time to First Token.
        
        Strategy:
        1. Parallel prefetch of weights on unused channels
        2. Channel striping for matrix multiplications
        3. Async KV cache initialization
        """
        # Use all channels for parallel prefill
        # Burst-aligned accesses maximize HBM4 efficiency
        seq_len = len(input_tokens)
        tokens_per_channel = seq_len // self.channels
        
        # Each channel processes a slice of the sequence
        for ch in range(self.channels):
            start = ch * tokens_per_channel
            end = start + tokens_per_channel if ch < self.channels - 1 else seq_len
            # Async transfer to compute unit
            self.async_transfer(input_tokens[start:end], channel=ch)
    
    def optimize_tpot(self, kv_cache_size):
        """
        Optimize Time per Output Token (decode phase).
        
        Critical path:
        1. KV cache read (random access, ~50 cycles)
        2. Attention computation
        3. KV cache write (sequential, ~20 cycles)
        4. MLP computation
        
        HBM4 optimization: Overlap KV reads with computation
        """
        # Preload next N tokens' KV cache while computing current
        prefetch_depth = 3  # Prefetch 3 tokens ahead
        
        for token_idx in range(len(kv_cache_size)):
            # Issue KV read for current token
            kv_read = self.read_kv_cache(token_idx, channel="current")
            
            # Issue prefetch for future tokens (non-blocking)
            for prefetch_offset in range(1, prefetch_depth + 1):
                future_token = token_idx + prefetch_offset
                if future_token < len(kv_cache_size):
                    self.prefetch_kv(future_token, 
                                    channel=f"ch{future_token % self.channels}")
            
            # Compute attention (overlaps with prefetch)
            self.compute_attention(kv_read)
            
            # Write back KV cache
            self.write_kv_cache(token_idx)
```

### 6.2 Memory Latency Hiding Techniques

```
┌────────────────────────────────────────────────────────────────────────┐
│                    HBM4 Command Queue Overlap                          │
│                                                                    │
│  Without Hiding:                                                   │
│  Cycle 0: READ request → 5 cycles → DATA → compute                 │
│                                                                    │
│  With Command Queue:                                               │
│  Cycle 0: READ cmd0 ───────────────────────────────┐               │
│  Cycle 1:        READ cmd1 ───────────────────────┐│               │
│  Cycle 2:              READ cmd2 ──────────────┐ │               │
│  Cycle 3:                    READ cmd3 ───────┐ │ │               │
│  Cycle 4:                          READ cmd4 ─┐ │ │ │             │
│  Cycle 5: DATA←cmd0 → compute ─────────────────┘ │ │             │
│  Cycle 6: DATA←cmd1 → compute ───────────────────┘ │             │
│  Cycle 7: DATA←cmd2 → compute ─────────────────────┘             │
│                                                                    │
│  Result: 4 commands pending = 4x latency hiding                   │
│          HBM4 32-channel system enables 32 parallel streams        │
└────────────────────────────────────────────────────────────────────┘
```

## 7. Multi-Query Attention (MQA) and Grouped-Query Attention (GQA)

### 7.1 HBM4 Optimization for Reduced KV Heads

```python
class GQAOptimizer:
    """
    Grouped-Query Attention reduces KV cache by sharing heads.
    
    MQA: 1 KV head per group
    GQA: 2-8 KV heads per group
    
    Memory reduction:
    - Standard MHA: N layers × 2 heads × seq_len × head_dim
    - MQA/GQA: Reduced proportional to KV head sharing
    """
    
    def __init__(self, num_kv_heads, num_q_heads):
        self.num_kv_heads = num_kv_heads
        self.num_q_heads = num_q_heads
        self.kv_head_ratio = num_q_heads / num_kv_heads
    
    def calculate_kv_cache_savings(self, seq_len, head_dim, num_layers):
        """
        Calculate memory savings from GQA vs MHA.
        """
        mha_cache = 2 * num_layers * seq_len * head_dim * num_q_heads * 2  # K+V
        gqa_cache = 2 * num_layers * seq_len * head_dim * self.num_kv_heads * 2
        
        reduction = mha_cache / gqa_cache
        
        return {
            "mha_cache_bytes": mha_cache * 2,  # BF16
            "gqa_cache_bytes": gqa_cache * 2,
            "memory_reduction": f"{reduction:.1f}x",
            "hbm4_channels_saved": int(32 * (1 - 1/reduction))
        }
```

## 8. Inference-Specific Error Handling

### 8.1 Inference Recovery Patterns

```python
class InferenceErrorRecovery:
    """
    Error handling optimized for inference workloads.
    
    Key difference from training:
    - Cannot recompute from gradients (no gradients during inference)
    - Recovery must use checkpoint or recompute from model
    """
    
    def __init__(self, model_checkpoint_path):
        self.checkpoint_path = model_checkpoint_path
        self.checkpoint_loader = CheckpointLoader()
    
    def handle_memory_error(self, failed_channel, address):
        """
        Handle HBM4 memory error during inference.
        
        Recovery strategies (in order of preference):
        1. Retry read (transient errors cleared in ~1 cycle)
        2. Re-read from model weights (static, always in HBM4)
        3. Restore from checkpoint (KV cache loss)
        """
        # Retry first (most transient errors)
        result = self.retry_read(failed_channel, address, max_retries=3)
        if result.success:
            return result
        
        # Check what type of data was corrupted
        data_type = self.classify_address(address)
        
        if data_type == "kv_cache":
            # KV cache corrupted - must regenerate
            # This is expensive but recoverable
            layer_idx = self.get_layer_from_address(address)
            return self.regenerate_kv_layer(layer_idx, address.seq_pos)
        
        elif data_type == "model_weights":
            # Weights corrupted - reload from checkpoint
            # Model weights are static, can be reloaded
            return self.reload_weights_from_checkpoint(address)
        
        elif data_type == "activations":
            # Activations corrupted - recompute from previous state
            return self.recompute_activations(address)
    
    def classify_address(self, address):
        """Classify address space for appropriate recovery."""
        # Implementation depends on address mapping
        pass
```

### 8.2 Inference Checkpoint Strategy

```
Checkpoint Strategy for Inference
──────────────────────────────────
Component          │  Persistence   │  Checkpoint Need │ Recovery Cost
──────────────────┼────────────────┼──────────────────┼────────────────
Model Weights     │  Permanent     │  Low (rarely bad)│  Load from disk
KV Cache          │  Ephemeral     │  High (session)  │  Regenerate
Request Queue     │  Recoverable   │  Medium          │  Re-queue
Position Counter  │  Ephemeral     │  None           │  Reset counter

KV Cache Checkpoint Recommendation
──────────────────────────────────
Session Duration  │  Checkpoint Strategy
─────────────────┼────────────────────────────────────────
< 1 minute       │  No checkpoint needed
1-10 minutes     │  Checkpoint every 30 seconds
> 10 minutes     │  Checkpoint every minute + prefix cache

Checkpoint Overhead (405B model example)
────────────────────────────────────────
KV Cache Size  │  HBM4 Write Time  │  Frequency
───────────────┼───────────────────┼─────────────────────────
128K context   │  ~500ms           │  Every 30 seconds
32K context   │  ~125ms           │  Every 30 seconds
8K context    │  ~30ms            │  Every 30 seconds
```

## 9. Performance Profiling for Inference

### 9.1 Inference-Specific Metrics

```python
class InferenceProfiler:
    """
    Profiling metrics specific to inference on HBM4.
    """
    
    INFERENCE_METRICS = {
        "time_to_first_token": {
            "description": "Latency from request to first output token",
            "target": "< 100ms for 7B model, < 500ms for 70B",
            "hbm4_indicator": "Prefill BW utilization"
        },
        "tokens_per_second": {
            "description": "Decode throughput",
            "target": "Model-dependent, ~50-100 tok/s for 7B",
            "hbm4_indicator": "Decode phase BW utilization"
        },
        "kv_cache_hit_rate": {
            "description": "KV cache locality",
            "target": "> 95% for coherent request streams",
            "hbm4_indicator": "Read/write ratio"
        },
        "channel_utilization_imbalance": {
            "description": "Balance across 32 channels",
            "target": "< 10% variance between channels",
            "hbm4_indicator": "Per-channel traffic monitoring"
        },
        "attention_memory_stalls": {
            "description": "Stalls waiting for KV cache",
            "target": "< 5% of total cycles",
            "hbm4_indicator": "Command queue depth"
        }
    }
    
    def report_inference_performance(self):
        """Generate inference performance report."""
        return {
            "ttft_ms": self.measure_ttft(),
            "tps": self.measure_tokens_per_second(),
            "kv_hit_rate": self.measure_kv_hit_rate(),
            "channel_balance": self.measure_channel_balance(),
            "memory_stalls_pct": self.measure_stalls()
        }
```

### 9.2 Bottleneck Patterns Specific to Inference

| Bottleneck Symptom | Root Cause | Solution |
|-------------------|------------|----------|
| High TTFT | Slow prefill | Increase prefetch, channel striping |
| Low TPS | Decode bottleneck | KV cache optimization, quantization |
| High KV read latency | Random access pattern | Channel striping, prefetch |
| Channel imbalance | Poor request batching | Group by seq_len, prefix cache |
| Growing latency over time | KV cache thrashing | Increase cache size, checkpoint |
| Prefill/decode imbalance | BW misallocated | Dynamic channel reallocation |

## 10. References

- HBM4 JEDEC JESD235C (when published)
- TensorRT-LLM documentation for inference optimization
- vLLM continuous batching implementation
- FalshAttention-2 for IO-aware attention
- LLM inference serving surveys (MLSys 2024)

## 11. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-15 | Initial version, complementary to ai_training_patterns.md |