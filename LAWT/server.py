#!/usr/bin/env python3
"""
LAWT前端服务器
提供静态文件服务和基本的矩阵计算功能
"""

import os
import json
import math
import numpy as np
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
import sys

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from lawt_model import get_lawt_manager
    LAWT_AVAILABLE = True
    print("✅ LAWT模型模块加载成功")
except ImportError as e:
    print(f"⚠️ LAWT模型模块加载失败: {e}")
    LAWT_AVAILABLE = False

try:
    from math_formatter import format_math_output
    MATH_FORMATTER_AVAILABLE = True
    print("✅ 数学格式化器加载成功")
except ImportError as e:
    print(f"⚠️ 数学格式化器加载失败: {e}")
    MATH_FORMATTER_AVAILABLE = False

try:
    from math_input_parser import parse_math_input
    MATH_INPUT_PARSER_AVAILABLE = True
    print("✅ 数学输入解析器加载成功")
except ImportError as e:
    print(f"⚠️ 数学输入解析器加载失败: {e}")
    MATH_INPUT_PARSER_AVAILABLE = False

try:
    from user_stats_db import get_db, generate_session_id
    DB_AVAILABLE = True
    print("✅ 用户统计数据库加载成功")
except ImportError as e:
    print(f"⚠️ 用户统计数据库加载失败: {e}")
    DB_AVAILABLE = False

class LAWTHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(__file__), 'frontend'), **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        # 首先处理图片文件
        if parsed_path.path.endswith('.jpg') or parsed_path.path.endswith('.jpeg') or parsed_path.path.endswith('.png'):
            self.serve_image()
        elif parsed_path.path == '/api/status':
            self.handle_status()
        elif parsed_path.path == '/api/stats':
            self.handle_stats()
        elif parsed_path.path == '/api/comments':
            self.handle_get_comments()
        elif parsed_path.path.startswith('/api/'):
            self.send_error(404, "API endpoint not found")
        else:
            # 默认处理静态文件
            super().do_GET()
    
    def serve_image(self):
        """处理图片请求"""
        parsed_path = urlparse(self.path)
        image_path = os.path.join(os.path.dirname(__file__), parsed_path.path.lstrip('/'))
        
        print(f"DEBUG: Requesting image at: {image_path}")
        print(f"DEBUG: Image exists: {os.path.exists(image_path)}")
        
        if os.path.exists(image_path) and image_path.endswith(('.jpg', '.jpeg', '.png')):
            try:
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                    self.send_response(200)
                    self.send_header('Content-type', f'image/{image_path.split(".")[-1]}')
                    self.send_header('Content-Length', str(len(image_data)))
                    self.end_headers()
                    self.wfile.write(image_data)
                    print(f"DEBUG: Image sent successfully: {image_path}")
            except Exception as e:
                print(f"DEBUG: Error reading image: {e}")
                self.send_error(500, f"Error reading image: {str(e)}")
        else:
            print(f"DEBUG: Image not found or invalid: {image_path}")
            self.send_error(404, "Image not found")
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/compute':
            self.handle_compute()
        elif parsed_path.path == '/api/comment':
            self.handle_post_comment()
        else:
            self.send_error(404, "API endpoint not found")
    
    def handle_status(self):
        """处理状态检查请求"""
        try:
            # 模拟模型状态检查
            status = {
                'model_available': True,
                'model_status': 'ready',
                'message': 'LAWT模型已就绪',
                'timestamp': time.time()
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
            
        except Exception as e:
            self.send_error(500, f"Status check failed: {str(e)}")
    
    def handle_compute(self):
        """处理矩阵计算请求"""
        try:
            # 读取请求数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 提取参数
            operation = data.get('operation')
            matrix_a = data.get('matrixA')
            matrix_b = data.get('matrixB')
            method = data.get('method', 'numpy')
            
            # 验证输入
            if not operation or not matrix_a:
                raise ValueError("缺少必要参数")
            
            # 解析输入数据（支持分数、根号等格式）
            if MATH_INPUT_PARSER_AVAILABLE:
                try:
                    matrix_a = parse_math_input(matrix_a)
                    if matrix_b is not None:
                        matrix_b = parse_math_input(matrix_b)
                except ValueError as e:
                    raise ValueError(f"输入解析失败: {str(e)}")
            
            # 执行计算
            if method == 'lawt':
                result = self.compute_with_lawt(operation, matrix_a, matrix_b)
            else:
                result = self.compute_with_numpy(operation, matrix_a, matrix_b)
            
            # 返回结果
            response = {
                'success': True,
                'result': result,
                'method': method,
                'operation': operation,
                'timestamp': time.time()
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            error_response = {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }
            
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
    
    def compute_with_lawt(self, operation, matrix_a, matrix_b=None):
        """使用真实的LAWT模型计算"""
        if not LAWT_AVAILABLE:
            raise Exception("LAWT模型不可用，请使用NumPy计算")
        
        try:
            # 获取LAWT模型管理器
            manager = get_lawt_manager()
            
            # 检查模型是否可用
            if not manager.is_model_available(operation):
                raise Exception(f"LAWT模型不支持 {operation} 操作")
            
            # 使用真实的LAWT模型计算
            result = manager.compute_with_lawt(operation, matrix_a, matrix_b)
            
            return result
            
        except Exception as e:
            # LAWT模型计算失败，不允许回退，直接抛出异常
            raise Exception(f"LAWT模型计算失败: {str(e)}")
    
    def compute_with_numpy(self, operation, matrix_a, matrix_b=None):
        """使用NumPy计算"""
        A = np.array(matrix_a)
        
        if matrix_b is not None:
            B = np.array(matrix_b)
        
        if operation == 'transpose':
            result = A.T
        elif operation == 'add':
            if matrix_b is None:
                raise ValueError("矩阵加法需要两个矩阵")
            result = A + B
        elif operation == 'multiply':
            if matrix_b is None:
                raise ValueError("矩阵乘法需要两个矩阵")
            result = np.dot(A, B)
        elif operation == 'inverse':
            try:
                result = np.linalg.inv(A)
            except np.linalg.LinAlgError:
                raise ValueError("矩阵不可逆")
        elif operation == 'eigenvalues':
            try:
                eigenvalues = np.linalg.eigvals(A)
                result = eigenvalues.tolist()
            except np.linalg.LinAlgError:
                raise ValueError("无法计算特征值")
        elif operation == 'eigenvectors':
            try:
                eigenvalues, eigenvectors = np.linalg.eig(A)
                result = {
                    'eigenvalues': eigenvalues.tolist(),
                    'eigenvectors': eigenvectors.T.tolist()  # 转置以匹配期望格式
                }
            except np.linalg.LinAlgError:
                raise ValueError("无法计算特征向量")
        else:
            raise ValueError(f"不支持的操作: {operation}")
        
        # 转换为Python列表
        if isinstance(result, np.ndarray):
            result = result.tolist()
        elif isinstance(result, dict):
            result = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in result.items()}
        
        # 使用数学格式化器格式化结果
        if MATH_FORMATTER_AVAILABLE:
            try:
                result = format_math_output(result, operation)
            except Exception as e:
                print(f"⚠️ 数学格式化失败: {e}")
                # 如果格式化失败，返回原始结果
        
        return result

    def handle_stats(self):
        """处理用户统计请求"""
        try:
            if not DB_AVAILABLE:
                stats = {
                    'total_users': 0,
                    'online_users': 0,
                    'popular_operation': '矩阵转置'
                }
            else:
                db = get_db()
                stats = db.get_user_stats()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
            
        except Exception as e:
            self.send_error(500, f"Stats request failed: {str(e)}")
    
    def handle_get_comments(self):
        """处理获取评论请求"""
        try:
            if not DB_AVAILABLE:
                comments = []
            else:
                db = get_db()
                comments = db.get_recent_comments(10)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(comments).encode())
            
        except Exception as e:
            self.send_error(500, f"Comments request failed: {str(e)}")
    
    def handle_post_comment(self):
        """处理提交评论请求"""
        try:
            # 读取请求数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            comment_text = data.get('comment', '').strip()
            session_id = data.get('session_id', 'anonymous')
            
            if not comment_text:
                raise ValueError("评论内容不能为空")
            
            if len(comment_text) > 100:
                raise ValueError("评论不能超过100字")
            
            # 记录评论
            if DB_AVAILABLE:
                db = get_db()
                db.get_or_create_user(session_id)
                db.record_comment(session_id, comment_text)
            
            response = {
                'success': True,
                'message': '评论提交成功',
                'timestamp': time.time()
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            error_response = {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }
            
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())

def run_server(port=8080):
    """启动服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, LAWTHandler)
    
    print(f"LAWT前端服务器启动在端口 {port}")
    print(f"访问地址: http://localhost:{port}")
    print("按 Ctrl+C 停止服务器")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        httpd.shutdown()

if __name__ == '__main__':
    import sys
    
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("端口号必须是整数")
            sys.exit(1)
    
    run_server(port)
