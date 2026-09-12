import os
import subprocess
import sys

def main():
    env = os.environ.copy()
    env['OLLAMA_KV_CACHE_TYPE'] = 'q8_0'
    env['OLLAMA_FLASH_ATTENTION'] = '1'
    env['OLLAMA_NUM_PARALLEL'] = '1'
    print('[*] Starting Ollama with OLLAMA_KV_CACHE_TYPE=q8_0, OLLAMA_FLASH_ATTENTION=1...', flush=True)
    subprocess.run(['ollama', 'serve'], env=env)

if __name__ == '__main__':
    main()
