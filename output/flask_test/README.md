# Flask测试项目

这是一个简单的Flask项目，包含基本的hello world路由。

## 功能
- `/` - 返回"Hello, World!"
- `/health` - 返回健康检查状态

## 安装依赖
```bash
pip install -r requirements.txt
```

## 运行应用
```bash
python app.py
```

## 运行测试
```bash
pytest
```

## 项目结构
```
flask_test/
├── app.py          # 主应用文件
├── test_app.py     # 测试文件
├── requirements.txt # 依赖文件
└── README.md       # 项目说明
```