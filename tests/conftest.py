# DataPulse
"""测试夹具"""
import os
import sys
import tempfile

import pytest

# 确保 backend 和 spider 在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "spider"))


@pytest.fixture
def sample_html():
    return """
    <html><head><title>测试页面</title></head>
    <body>
        <h1>Hello World</h1>
        <table>
            <thead><tr><th>商品</th><th>价格</th></tr></thead>
            <tbody>
                <tr><td>商品A</td><td>99</td></tr>
                <tr><td>商品B</td><td>199</td></tr>
            </tbody>
        </table>
        <a href="/page1">页面1</a>
        <a href="/page2">页面2</a>
    </body></html>
    """


@pytest.fixture
def sample_csv():
    import pandas as pd
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35],
        "score": [85.5, 90.0, 78.3],
    })
    return df


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
