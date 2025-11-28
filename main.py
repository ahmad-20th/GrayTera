import argparse
import sys
import signal
import logging
from pathlib import Path
from core.pipeline import Pipeline
from core.data_store import DataStore
from observers.console_observer import ConsoleObserver
from observers.file_observer import FileObserver
from utils.logger import setup_logging
from utils.output import error, success, info
from utils.cve_mapper import CVEMapper

SCRIPT_DIR = Path(__file__).parent.absolute()
pipeline = None

def print_banner():
    banner = """
    ╔═══════════════════════════════════════╗
    ║            GrayTera v1.0              ║
    ║   Advanced Pentesting Automation      ║
    ╚═══════════════════════════════════════╝
    """
    print(banner)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n[!] Scan interrupted. Saving state...")
    if pipeline:
        pipeline.pause()
    print("[✓] State saved. Use --resume to continue.")
    sys.exit(0)

def validate_files(args):
    """Validate that required files exist"""
    if not Path(args.config).exists():
        error(f"Config file not found: {args.config}")
        return False
    
    if args.scope and not Path(args.scope).exists():
        error(f"Scope file not found: {args.scope}")
        return False
    
    return True

def main():
    global pipeline
    
    print_banner()

    # Argument parsing
    parser = argparse.ArgumentParser(
        description='GrayTera DAST Pentesting Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('target', help='Target domain (e.g., example.com)')
    parser.add_argument('--resume', action='store_true', 
                       help='Resume previous scan')
    parser.add_argument('--stage', choices=['enum', 'filter', 'validate', 'scan', 'exploit'], 
                       help='Run specific stage only')
    parser.add_argument('--output', default='data/scans', 
                       help='Output directory (default: data/scans)')
    parser.add_argument('--config', default='config.yaml', 
                       help='Config file (default: config.yaml)')
    parser.add_argument('--scope', 
                       help='Scope file (scope.json) for pentest scope filtering')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose output')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    parser.add_argument('--interactive', action='store_true',
                       help='Pause between stages to review results')
    parser.add_argument('--version', action='version', version='GrayTera v1.0')
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute paths based on script directory
    if not Path(args.config).is_absolute():
        args.config = str(SCRIPT_DIR / args.config)
    if args.scope and not Path(args.scope).is_absolute():
        args.scope = str(SCRIPT_DIR / args.scope)
    if not Path(args.output).is_absolute():
        args.output = str(SCRIPT_DIR / args.output)
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Validate target domain
    from utils.validators import is_valid_domain
    if not is_valid_domain(args.target):
        error(f"Invalid domain: {args.target}")
        sys.exit(1)
    
    # Validate files exist
    if not validate_files(args):
        sys.exit(1)
    
    # Setup logging (only for file logs, not console)
    try:
        setup_logging()
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        elif args.verbose:
            logging.getLogger().setLevel(logging.INFO)
        else:
            # Suppress console logging unless debug/verbose
            logging.getLogger().setLevel(logging.WARNING)
    except Exception as e:
        error(f"Logging setup failed: {e}")
        sys.exit(1)
    
    # Create output directory
    try:
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        error(f"Failed to create output directory: {e}")
        sys.exit(1)
    
    # Initialize data store
    try:
        data_store = DataStore(args.output)
    except Exception as e:
        error(f"Data store initialization failed: {e}")
        sys.exit(1)
    
    # Create pipeline with observers
    try:
        pipeline = Pipeline(data_store, config_path=args.config, scope_file=args.scope, interactive=args.interactive)
        pipeline.attach(ConsoleObserver())
        pipeline.attach(FileObserver(args.output))
    except Exception as e:
        error(f"Pipeline initialization failed: {e}")
        sys.exit(1)
    
    # Execute pipeline
    try:
        if args.resume:
            # Check if there's something to resume
            if not pipeline.can_resume(args.target):
                error(f"No previous scan found for {args.target}")
                sys.exit(1)
            
            pipeline.resume(args.target)
        else:
            pipeline.run(args.target, specific_stage=args.stage)
        
        # Success message
        success("Scan completed successfully!")
        info(f"Results saved to: {output_path.absolute()}")
        
    except KeyboardInterrupt:
        # Should be caught by signal handler, but just in case
        print("\n[!] Scan interrupted.")
        sys.exit(0)
    except Exception as e:
        error(f"Error during execution: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()