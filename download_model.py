# 使用modelscope sdk下载模型
if __name__ == '__main__':
    from modelscope import snapshot_download
    model_dir = snapshot_download('opendatalab/PDF-Extract-Kit')
    print(f"模型文件下载路径为：{model_dir}/models")