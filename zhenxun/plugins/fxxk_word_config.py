from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_config_path = Path(__file__).with_name("fxxk_word_config_local.py")
if not _config_path.exists():
    raise RuntimeError("缺少本地配置：请复制 fxxk_word_config.example.py 为 fxxk_word_config_local.py 并填写真实配置。")

_spec = spec_from_file_location("fxxk_word_config_local", _config_path)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"无法加载本地配置：{_config_path}")

_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)
globals().update({key: value for key, value in vars(_module).items() if not key.startswith("_")})
