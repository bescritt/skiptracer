# Skiptracer — OSINT web-scraping framework

![banner](artwork/banner.png)

![python](https://img.shields.io/badge/python-3.13-blue.svg)
![version](https://img.shields.io/badge/version-4.0.0-brightgreen.svg)
![license](https://img.shields.io/badge/license-Apache%202.0-lightgrey.svg)

Initial attack vectors for recon usually involve pay-for-data / API services
(Recon-NG) or paid transforms (Maltego) to yield data-mining results. Skiptracer
performs basic Python web scraping (BeautifulSoup) against PII paywall sites to
compile passive information on a target while spending almost nothing.

## Background

The following recording from DEF CON 26 Recon Village provides background on
Skiptracer:

[DEFCON 26 Recon Village — Skiptracer Talk](https://www.youtube.com/watch?v=3mEOkwrxfsU)

## Installation

### From source

```bash
$ git clone https://github.com/bescritt/skiptracer.git
$ cd skiptracer
$ python3 -m venv .venv
$ .venv/bin/python -m pip install -e .
```

### Run

```bash
$ python3 -m skiptracer
```

### With Docker

```bash
$ docker-compose run --rm skiptracer
```

The `--rm` flag removes the container after execution.

## Usage

After launch, the menu system guides navigation between plugins. Each plugin
requests its parameters through the menu prompts.

Supported lookup types include:

* Phone
* Email
* Screen names
* Real names
* Addresses
* Breach credentials
* License plates

The plugin framework lets contributors submit new modules for additional sites,
which grows the collected data with minimal effort. Skiptracer serves as a
one-stop shop for assembling relevant target information and widening the
attack surface.

## Configuration and extension

### Plugins

Skiptracer uses a plugin architecture. Place plugins under:

```
src/skiptracer/plugins/<plugin_name>/
```

Each plugin folder needs `__init__.py` and `__main__.py`. Register the plugin
in `setup.py` under the `skiptracer.plugins` entry-points group:

```python
'skiptracer.plugins': [
    'myplugin = skiptracer.plugins.myplugin:MyNewSiteGrabber',
]
```

Supply plugin parameters through `src/skiptracer/data/skiptracer.cfg`:

```ini
[plugin.myplugin]
homepageurl = https://www.example.com
loginurl = https://www.example.com/uas/login-submit
```

Set those values through the command line or via a `.env` file.

### Plugin menu configuration

The menu system reads `src/skiptracer/data/skiptracer.cfg`. When adding a plugin,
list it under the menu sections where it should appear. A plugin may appear under
several menus.

```ini
[menu.email]
myplugin = ["My Plugin", "Check if user exposes information through some site"]
```

### Tests

The suite uses pytest with mocked HTTP. Execute it with:

```bash
$ python3 -m pytest test/ -v
```

## License

Apache License 2.0. See `LICENSE` for the full text.

## Agent adapters and runbook
A hermes-brain style adapter lives in `tools/agent_adapters.py` with a short runbook in `docs/AGENT_RUNBOOK.md`. It provides parallel_probe, retries, verification, synthesis, and persistence helpers to safely orchestrate plugin calls.

HIBP plugin: the haveibeenpwned plugin uses the HIBP v3 API and requires an API key via HAVEIBEENPWNED_API_KEY or HIBP_API_KEY environment variable. The plugin no longer uses cfscrape and parses JSON safely. See docs/AGENT_RUNBOOK.md for details.
