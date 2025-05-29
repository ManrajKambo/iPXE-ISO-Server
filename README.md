# iPXE ISO Web Server

A lightweight Flask-based web application that dynamically generates an iPXE boot menu from an `Images.json` configuration file. Simply drop your ISO files into a mount directory, update `Images.json` with friendly labels or web links, and the server will automatically rebuild and serve an iPXE boot script.

---

## Features

* **Dynamic Menu Generation**
  Reads `Images.json` on each request; any changes are picked up automatically.
* **Local & Remote ISOs**
  Support for local ISO files in the `mount/` directory or remote URLs.
* **Automatic "Other" Category**
  Untracked ISOs in `mount/` will be grouped under an `Other` section.
* **Dual Boot Methods**

  * Type 1: Memdisk + initrd chainloading
  * Type 2: Direct `sanboot` chaining (default)
* **Caching & Timestamps**
  Script outputs are cached in memory, and an `X-Last-Updated` header shows when the menu last changed.
* **Simple File Serving**
  Static ISO downloads via `/<filesDir>/<filename>` endpoint.

---

## Prerequisites

* Docker
* Access to a machine that can serve HTTP (ports 80 or custom)

---

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/ManrajKambo/ipxe-iso-server.git
   cd ipxe-iso-server
   ```

2. Install Docker (For Debian 12):
   ```bash
    apt-get update; \
    apt-get install -y ca-certificates curl; \
    install -m 0755 -d /etc/apt/keyrings; \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc; \
    chmod a+r /etc/apt/keyrings/docker.asc; \
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null; \
    apt-get update; \
    apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```

---

## Directory Layout

```text
├── app.py            # Entry point
├── iPXE.py           # Core server implementation
├── iPXE.tpl          # Jinja2 template for menu.ipxe
├── Images.json       # Config file for ISO categories and labels
├── mount/            # Directory to place your own .iso files
└── files/            # Served file tree (relative URLs)
```

---

## Configuration (`Images.json`)

The JSON file controls which ISOs appear in the menu and how they are labeled. Example:

```json
{
	"Categories": {
		"VMware ESXi": {
			"VMware ESXI 6.7.0 Update 3 (Build 15160138)": "VMware-VMvisor-Installer-201912001-15160138.x86_64.iso",
			"VMware ESXI 7.0 Update 3 (Build 21930508)": "VMware-VMvisor-Installer-7.0U3n-21930508.x86_64.iso",
			"VMware ESXI 8.0 Update 3 (Build 24022510)": "VMware-VMvisor-Installer-8.0U3-24022510.x86_64.iso"
		},
		"Debian": {
			"Debian 12 (12.11.0)": "debian-12.11.0-amd64-netinst.iso"
		},
		"Ubuntu": {
			"Ubuntu 24.04.2 (Link)": "https://releases.ubuntu.com/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
		},
		"FreeBSD": {
			"FreeBSD 14.2 (Link)": "https://download.freebsd.org/releases/amd64/amd64/ISO-IMAGES/14.2/FreeBSD-14.2-RELEASE-amd64-bootonly.iso"
		},
		"Tools and utilities": {
			"System Rescue v10.02": "systemrescue-10.02-amd64.iso",
			"System Rescue v12.01 (Link)": "https://fastly-cdn.system-rescue.org/releases/12.01/systemrescue-12.01-amd64.iso"
		}
	},
	"Memdisk": "memdisk-5.10"
}
```

* **Categories**: Top-level grouping (e.g., `ISOs`, `Tools`).
* **Key**: Friendly label shown in the iPXE menu.
* **Value**: Local filename or full URL.
* **Memdisk**: Filename of `memdisk` binary in `mount/` for type-1 boots.

After you drop new ISO files into `mount/`, the server will detect any filenames not listed in `Categories` and auto-add them under a generated `Other` category.

---

## Usage

1. **Upload ISOs**
   Copy or download your `.iso` files into the `mount/` directory.

2. **Edit `Images.json`**
   Add, remove, or rename entries under `Categories`. Use URLs for remote ISOs.

3. **Run the Server**

   ```bash
   docker compose up --build -d
   ```

4. **Access the Menu**

   * Default boot script (sanboot):

     ```
     http://<host>:<port>/menu.ipxe
     ```

   * Memdisk mode (Doesn't work with Netboot.xyz):

     ```
     http://<host>:<port>/menu.ipxe?type=2
     ```

5. **Boot via iPXE**
   In your iPXE prompt:

   ```ipxe
   chain http://<host>:<port>/menu.ipxe
   ```

---

## How It Works

1. **Flask Endpoints**

   * `/menu.ipxe`: Renders iPXE script via Jinja2.
   * `/<filesDir>/<filename>`: Serves files from `mount/`.

2. **JSON Parsing & Caching**

   * On each request, `Images.json` is loaded.
   * Untracked `.iso` files are auto-added under `Other`.
   * If the menu data changed, scripts for type-1 and type-2 are re-generated and cached.

3. **Script Generation**

   * Jinja2 template (`iPXE.tpl`) injects menu items and boot sections.
   * Each item gets a sanitized key (alphanumeric + dashes).
   * `sanboot` or `memdisk + initrd chain` commands are populated.

4. **Headers & Metadata**

   * The `X-Last-Updated` header exposes the UTC timestamp of last regeneration.

---

## Customization

* **Change Host/Port**: Modify parameters in `app.py` / `docker-compose.yml`
* **Serve Over HTTPS**: Place a reverse proxy (Nginx, Caddy) in front.
* **Template Tweaks**: Edit `iPXE.tpl` for custom styling, banners, or timeouts.

---

## Troubleshooting

* **JSON Parse Errors**: Ensure `Images.json` is valid JSON.
* **Missing Files**: Check `mount/` permissions and paths.
* **iPXE Errors**: Try switching `type` parameter between `1` and `2`.

---

## Contributing

1. Fork the repo.
2. Create a feature branch (`git checkout -b feature/foo`).
3. Commit your changes (`git commit -am 'Add feature'`).
4. Push to the branch (`git push origin feature/foo`).
5. Open a Pull Request.

---

## License

<details open>
<summary>License</summary>
<b>This project is licensed under the MIT License. See the <a href="LICENSE">LICENSE</a> file for details.</b>
</details>