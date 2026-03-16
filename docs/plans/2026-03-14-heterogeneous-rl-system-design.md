# OpenYoung 异构硬件适配的混合 RL 系统设计方案

> 基于 OpenManus-RL、VeRL、RAGEN 等最新研究成果
> 结合项目现状与 Docker 部署需求的完整设计
> 生成时间: 2026-03-14

---

## 一、技术背景与研究

### 1.1 LLM+RL 技术格局

| 框架 | 优势 | 局限 | 适用场景 |
|------|------|------|----------|
| **VeRL** (字节) | 生产级、多轮RL、400+回合 | 需要GPU集群 | 大规模训练 |
| **RAGEN/StarPO** | 多轮交互、推理能力 | 实现复杂 | 交互式Agent |
| **GiGPO** (OpenManus) | 细粒度信用分配 | 需大量GPU | 多步工具调用 |
| **GRPO** (DeepSeek-R1) | 无需价值函数、内存高效 | 单轮优化 | 推理增强 |
| **Verlog** (CMU) | 长序列、多变长episode | 新框架 | 超长任务 |

### 1.2 核心科学问题

```
问题1: 如何在异构硬件上实现高效的策略优化？
  └─> 方案: 分层抽象 - Hardware Abstraction Layer (HAL)

问题2: 如何平衡训练效率与内存占用？
  └─> 方案: 混合精度训练 + 梯度累积

问题3: 如何支持多轮交互的信用分配？
  └─> 方案: GiGPO 两层优势估计 + GAE
```

### 1.3 关键论文

- **GiGPO**: NeurIPS 2025 - Group-in-Group Policy Optimization for LLM Agent Training
- **Verlog**: CMU 2025 - Multi-turn RL framework for LLM agents
- **DeepSeek-R1**: 2025 - GRPO for reasoning models
- **RAGEN**: 2025 - Self-Evolving LLM Agents via Multi-Turn RL

---

## 二、系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         OpenYoung RL System                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Configuration Layer (YAML)                      │   │
│  │   rl: enabled / mode / device / hardware                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │           Hardware Abstraction Layer (HAL)                  │   │
│  │  HardwareDetector + DeviceManager + ComputeBackend          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    RL Engine (可切换)                        │   │
│  │  CollectionOnly | GRPO Engine | GiGPO Engine             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Experience Layer (已有)                          │   │
│  │   ExperienceEngine → SQLite → Qwen Embedding              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 硬件适配矩阵

| 硬件平台 | 加速方案 | 适用模式 | Docker 支持 |
|----------|----------|----------|-------------|
| NVIDIA GPU | CUDA + MPS | GRPO/GiGPO | nvidia-docker |
| Apple M1/M2 | Metal + MPS | GRPO | Rosetta + 容器 |
| RK3588 | Vulkan/NPU | GRPO | ARM 容器 |
| CPU | NumPy | Collection Only | 通用 |

---

## 三、核心组件

### 3.1 Hardware Abstraction Layer

```python
class ComputeBackend(Enum):
    CUDA = "cuda"    # NVIDIA GPU
    MPS = "mps"     # Apple Silicon
    CPU = "cpu"     # CPU only
    VULKAN = "vulkan"  # ARM GPU

class HardwareDetector:
    @staticmethod
    def detect() -> HardwareSpec:
        # 1. CUDA -> 2. MPS -> 3. Vulkan -> 4. CPU
        pass

class DeviceManager:
    def to_device(self, tensor):
        return tensor.to(self.device)
```

### 3.2 GRPO Engine

核心算法 (DeepSeek-R1):
- 无需价值函数，内存效率高
- 组内相对排名优势估计
- PPO-style 裁剪更新

```python
class GRPOEngine:
    def compute_advantages(self, rewards, mask):
        # 组均值归一化
        returns = (rewards * mask).sum(dim=-1)
        advantages = returns - returns.mean(dim=1, keepdim=True)
        return advantages

    def update_policy(self, log_probs, new_log_probs, advantages, mask):
        ratio = torch.exp(new_log_probs - log_probs)
        clipped = torch.clamp(ratio, 1 - eps, 1 + eps)
        loss = -torch.min(ratio * advantages, clipped * advantages)
        return loss
```

### 3.3 GiGPO Engine

核心创新 (OpenManus-RL):
- Episode-level 优势: 任务级别评估
- Step-level 优势: 步骤级别细粒度评估
- 两层融合: A = A_episode + λ × A_step

---

## 四、配置设计

### 4.1 主配置

```yaml
# config/rl.yaml
rl:
  enabled: true
  mode: collection_only  # collection_only | grpo | gigpo
  device: auto  # auto | nvidia | metal | cpu

  hardware:
    auto_detect: true
    nvidia:
      enabled: true
      cuda_devices: [0, 1]
    apple_silicon:
      enabled: true
      use_mps: true

  grpo:
    learning_rate: 1.0e-5
    clip_epsilon: 0.2
    kl_beta: 0.01
    group_size: 4

  gigpo:
    episode_advantage_weight: 1.0
    step_advantage_weight: 0.5
    use_gae: true
```

### 4.2 Docker 配置

```yaml
# docker-compose.yml
services:
  openyoung:
    build: .
    environment:
      - RL_ENABLED=true
      - RL_MODE=collection_only
      - RL_DEVICE=auto
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## 五、API 接口

```python
from src.agents.rl import RLEngine, RLConfig, HardwareDetector

# 自动检测硬件
hardware = HardwareDetector.detect()

# 创建引擎
config = RLConfig(enabled=True, mode="grpo")
engine = RLEngine(config, hardware)

# 训练
for batch in buffer:
    advantages = engine.compute_advantages(batch)
    losses = engine.update(batch, advantages)
```

---

## 六、测试

### 测试文件

```
tests/rl/
├── __init__.py
├── test_hardware.py       # 硬件抽象层测试
├── test_grpo.py           # GRPO 引擎测试
├── test_gigpo.py          # GiGPO 引擎测试
└── test_rl_engine.py      # 统一引擎集成测试
```

### 测试结果

```bash
$ python3 -m pytest tests/rl/ -v
================== 33 passed, 12 skipped ==================
```

注: 12 个测试因无 PyTorch 环境被跳过。

### 测试覆盖

| 模块 | 测试内容 |
|------|---------|
| hardware.py | ComputeBackend, HardwareSpec, HardwareDetector, DeviceManager |
| grpo_engine.py | GRPOConfig, GRPOEngine, 优势计算, 裁剪函数 |
| gigpo_engine.py | GiGPOConfig, GiGPOEngine, GAE, 两层优势融合 |
| engine.py | RLEngine, 模式切换, 硬件推荐 |

---

## 六、验收标准

1. **硬件检测**: 自动检测 CUDA/MPS/CPU 并选择最优后端
2. **模式切换**: 支持 collection_only/grpo/gigpo 三种模式
3. **Docker 兼容**: 能在 nvidia-docker 环境中运行
4. **性能指标**:
   - GRPO 模式可在 M1 Mac 上运行
   - GiGPO 模式可在单卡 A100 上运行
5. **向后兼容**: 现有经验收集功能不受影响
6. **测试通过**: 33 passed, 12 skipped (无 PyTorch)

---

## 七、参考资料

1. GiGPO: https://arxiv.org/abs/2505.10978
2. Verlog: https://blog.ml.cmu.edu/2025/09/15/verlog/
3. DeepSeek-R1: https://arxiv.org/abs/2501.12948
4. RAGEN: https://ragen-ai.github.io/
5. VeRL: https://github.com/verl-org/verl
