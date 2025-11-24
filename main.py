import argparse
import sys
from pathlib import Path
from core.pipeline import Pipeline
from core.data_store import DataStore
from observers.console_observer import ConsoleObserver
from observers.file_observer import FileObserver
from utils.logger import setup_logging

def print_banner():
    banner = """
    ╔═══════════════════════════════════════╗
    ║            GrayTera v1.0              ║
    ║   Advanced Pentesting Automation      ║
    ╚═══════════════════════════════════════╝
    """
    print(banner)

def main():
    print_banner()

    parser = argparse.ArgumentParser(description='GrayTera DAST Pentesting Tool')
    parser.add_argument('target', help='Target domain (e.g., example.com)')
    parser.add_argument('--resume', action='store_true', help='Resume previous scan')
    parser.add_argument('--stage', choices=['enum', 'scan', 'exploit'], 
                       help='Run specific stage only')
    parser.add_argument('--output', default='data/scans', help='Output directory')
    parser.add_argument('--config', default='config.yaml', help='Config file')
    args = parser.parse_args()
    
    # Validate target domain
    from utils.validators import is_valid_domain
    if not is_valid_domain(args.target):
        print(f"[!] Invalid domain: {args.target}")
        sys.exit(1)
    
    # Setup
    try:
        setup_logging()
    except Exception as e:
        print(f"[!] Logging setup failed: {e}")
        sys.exit(1)
    
    try:
        data_store = DataStore(args.output)
    except Exception as e:
        print(f"[!] Data store initialization failed: {e}")
        sys.exit(1)
    
    # Create pipeline with observers
    try:
        pipeline = Pipeline(data_store, config_path=args.config)
        pipeline.attach(ConsoleObserver())
        pipeline.attach(FileObserver(args.output))
    except Exception as e:
        print(f"[!] Pipeline initialization failed: {e}")
        sys.exit(1)
    
    try:
        if args.resume:
            pipeline.resume(args.target)
        else:
            pipeline.run(args.target, specific_stage=args.stage)
    except KeyboardInterrupt:
        print("\n[!] Scan paused. Use --resume to continue.")
        pipeline.pause()
        sys.exit(0)
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

