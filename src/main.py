import yaml
import time
from core.algorithms import IncrementalOptimizer
from network.udp_server import UDPServer
from utils.logger import setup_logger

# 通信
# 加载配置
def load_config(path="config/settings.yaml"):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    logger = setup_logger()

    try:
        config = load_config()  # 确保 config/settings.yaml 文件存在且格式正确
    except Exception as e:
        logger.critical(f"Config Load Failed: {e}")
        return

    # 初始化模块
    try:
        # [修复] 这里传递整个 config 字典，而不是 config['algorithm']
        optimizer = IncrementalOptimizer(config)

        server = UDPServer(
            config['network']['host'],
            config['network']['port'],
            config['network']['buffer_size']
        )
    except Exception as e:
        logger.critical(f"System Startup Failed: {e}")
        return

    logger.info(">>> AI Navigation System Started <<<")
    logger.info(f"Listening on {config['network']['host']}:{config['network']['port']}")

    iteration = 0
    try:
        while True:
            # 1. 接收
            data, client_addr = server.receive()
            if not data:
                # 防止空循环过快占用CPU
                time.sleep(0.01)
                continue

            # 2. 处理
            next_pos, chosen_idx, comp_name = optimizer.step(
                data['agent'],
                data['target'],
                data['obstacles']
            )

            # 3. 发送
            response = {
                'next_pos': next_pos,
                'chosen_component': chosen_idx
            }
            server.send(response, client_addr)

            # 4. 日志 (采样打印)
            iteration += 1
            if iteration % 20 == 0:
                logger.info(f"Iter {iteration} | Mode: {config['algorithm']['mode']} | Component: {comp_name}")

    except KeyboardInterrupt:
        logger.info("Server stopping...")
    except Exception as e:
        logger.error(f"Runtime Error: {e}")
    finally:
        if 'server' in locals():
            server.sock.close()


if __name__ == "__main__":
    main()