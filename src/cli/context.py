"""
CLI Context - 共享上下文
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class CLIContext:
    """CLI 共享上下文"""

    config_dir: Path = Path.home() / ".openyoung"
    verbose: bool = False
    debug: bool = False
    output_format: str = "text"  # text, json, yaml

    def __post_init__(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)

    @property
    def config_file(self):
        return self.config_dir / "config.json"

    @property
    def data_dir(self):
        return self.config_dir / "data"

    def load_config(self) -> dict:
        """加载配置"""
        import json

        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text())
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        return {}

    def save_config(self, config: dict) -> bool:
        """保存配置"""
        import json

        try:
            self.config_file.write_text(json.dumps(config, indent=2))
            return True
        except Exception as e:
            print(f"Config save error: {e}")
            return False
