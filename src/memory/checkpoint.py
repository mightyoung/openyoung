"""
CheckpointManager - 检查点管理器
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


class CheckpointManager:
    """Checkpoint 管理器

    负责创建、恢复和列出文件检查点
    """

    def __init__(self, checkpoint_dir: str = ".young/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_checkpoints = 10

    async def create_checkpoint(
        self, file_path: str, reason: str = "edit"
    ) -> Optional[str]:
        """创建检查点

        Args:
            file_path: 文件路径
            reason: 创建原因

        Returns:
            checkpoint_id 或 None（文件不存在）
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        # 生成唯一 ID
        checkpoint_id = f"{file_path.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 存储路径
        checkpoint_path = self.checkpoint_dir / checkpoint_id
        checkpoint_path.mkdir(parents=True, exist_ok=True)

        # 复制文件
        shutil.copy2(file_path, checkpoint_path / file_path.name)

        # 保存元数据
        metadata = {
            "checkpoint_id": checkpoint_id,
            "original_path": str(file_path),
            "reason": reason,
            "created_at": datetime.now().isoformat(),
            "file_size": file_path.stat().st_size,
        }

        with open(checkpoint_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        # 清理旧检查点
        await self._cleanup_old_checkpoints(file_path.name)

        return checkpoint_id

    async def restore_checkpoint(
        self, checkpoint_id: str, target_path: Optional[str] = None
    ) -> bool:
        """恢复检查点

        Args:
            checkpoint_id: 检查点 ID
            target_path: 目标路径（可选）

        Returns:
            是否成功
        """
        checkpoint_path = self.checkpoint_dir / checkpoint_id

        if not checkpoint_path.exists():
            return False

        # 读取元数据
        with open(checkpoint_path / "metadata.json") as f:
            metadata = json.load(f)

        original_path = target_path or metadata["original_path"]

        # 恢复文件
        source_file = checkpoint_path / Path(original_path).name
        shutil.copy2(source_file, original_path)

        return True

    async def list_checkpoints(
        self, file_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出检查点

        Args:
            file_path: 可选的过滤文件路径

        Returns:
            检查点列表
        """
        checkpoints = []

        for checkpoint_dir in self.checkpoint_dir.iterdir():
            if not checkpoint_dir.is_dir():
                continue

            metadata_file = checkpoint_dir / "metadata.json"
            if not metadata_file.exists():
                continue

            with open(metadata_file) as f:
                metadata = json.load(f)

            # 如果指定了文件路径，则过滤
            if file_path and metadata.get("original_path") != file_path:
                continue

            checkpoints.append(metadata)

        # 按创建时间排序
        checkpoints.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return checkpoints

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        checkpoint_path = self.checkpoint_dir / checkpoint_id

        if not checkpoint_path.exists():
            return False

        shutil.rmtree(checkpoint_path)
        return True

    async def _cleanup_old_checkpoints(self, file_name: str):
        """清理旧检查点"""
        # 获取该文件的所有检查点
        checkpoints = await self.list_checkpoints()
        file_checkpoints = [
            cp for cp in checkpoints if cp.get("original_path", "").endswith(file_name)
        ]

        # 删除超过限制的旧检查点
        if len(file_checkpoints) > self.max_checkpoints:
            for cp in file_checkpoints[self.max_checkpoints :]:
                await self.delete_checkpoint(cp["checkpoint_id"])
