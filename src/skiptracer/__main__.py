from .skiptracer import SkipTracer
from .banner import Banner


def main():
    """Start skip tracer."""
    plugins = 'all'
    banner = Banner()
    banner.banner()
    skiptracer = SkipTracer(plugins)


if __name__ == "__main__":
    main()
