from flask import Flask, make_response, request, send_from_directory
from werkzeug.utils import secure_filename
from waitress import serve
import json
import os
from glob import glob
from jinja2 import Environment, FileSystemLoader
from typing import Dict
from datetime import datetime

class iPXE:
	def __init__(self, host: str = "0.0.0.0", port: int = 80, serverHeader: str = "iPXE", mountDir: str = "/mount", filesDir: str = "files", imageJsonFile: str = "/Images.json"):
		self.__host = host
		self.__port = port
		self.__server_header = serverHeader
		self.__mount_dir = mountDir
		self.__files_dir = filesDir
		self.__image_json_file = imageJsonFile

		# Setup flask
		self.__app = self.__setup_flask()

		self.__ipxe_menu_data = {
			"Categories": {
			},
			"Memdisk": False
		}

		self.__ipxe_cache_1 = None
		self.__ipxe_cache_2 = None
		self.__last_updated = None

	# Setup flask server and add endpoints
	def __setup_flask(self):
		app = Flask(__name__)

		allowed_methods = ["GET"]

		# /menu.ipxe (iPXE Menu endpoint)
		app.add_url_rule("/menu.ipxe", view_func=self.__get_menu, methods=allowed_methods)

		# /files/file_to_download.txt (File endpoint)
		app.add_url_rule(f"/{self.__files_dir}/<path:filename>", view_func=self.__get_file, methods=allowed_methods)

		return app

	# Create Flask response with response headers
	def __return(self, content, status_code, headers = {}):
		resp = make_response(content, status_code) if status_code else make_response(content)

		if headers:
			for header, value in headers.items():
				resp.headers[header] = value

		return resp

	# Get the iPXE menu data
	def __get_ipxe_menu_data(self) -> bool:
		if not os.path.isfile(self.__image_json_file):
			return False

		with open(self.__image_json_file, "r") as f:
			try:
				data = json.loads(f.read())
			except json.JSONDecodeError:
				return False

		# Collect already added .iso filenames
		added_isos = [v for cat in data.get("Categories", {}).values() for v in cat.values()]

		# Collect all .iso files from mount directory
		not_added_isos = glob(f"{self.__mount_dir}/*.iso")

		# Filter untracked .iso files
		untracked = [
			os.path.basename(iso)
			for iso in not_added_isos
			if os.path.basename(iso) not in added_isos
		]

		# Only add "Other" category if there are untracked ISOs
		if untracked:
			data["Categories"].setdefault("Other", {})
			other_count = len(data["Categories"]["Other"])
			for i, iso in enumerate(untracked, start=other_count + 1):
				data["Categories"]["Other"][f"iso_{i}: {iso}"] = iso

		self.__ipxe_menu_data = data
		return True

	def __generate_ipxe_script(self, type: int) -> str:
		data: Dict = self.__ipxe_menu_data
		base_url = f"{request.scheme}://{request.host}:{request.environ.get('SERVER_PORT')}/{self.__files_dir}/"

		menu_items = ""
		boot_sections = ""

		for category, entries in data.get("Categories", {}).items():
			if not entries:
				continue

			menu_items += f"item --gap --   --- {category} ---\n"

			for name, filename in entries.items():
				key_id = self.__generate_key(name)
				label = name.strip()
				menu_items += f"item --key v {key_id} {label}\n"

				url = filename if "://" in filename else f"${{base-url}}{filename}"

				if type == 1:
					boot_sections += f":{key_id}\necho Booting {label}...\n\ninitrd {url}\nchain ${{base-url}}{self.__ipxe_menu_data['Memdisk']} iso || goto failed\ngoto start\n\n"
				elif type == 2:
					#boot_sections += f":{key_id}\necho Booting {label}...\n\nsanboot --no-describe --drive 0x80 {url} || goto failed\ngoto start\n\n"
					boot_sections += f":{key_id}\necho Booting {label}...\n\nsanboot {url} || goto failed\ngoto start\n\n"
				else:
					return False

			menu_items += "item\n"

		# Load and render the template
		env = Environment(loader=FileSystemLoader(searchpath='.'))
		template = env.get_template("iPXE.tpl")

		return template.render(
			base_url=base_url,
			menu_items=menu_items.strip(),
			boot_sections=boot_sections.strip()
		)

	def __generate_key(self, name: str) -> str:
		return ''.join(c.lower() if c.isalnum() else '-' for c in name).strip('-')

	# Get the iPXE menu
	def __get_menu(self) -> str:
		old_data = self.__ipxe_menu_data.copy()

		if not self.__get_ipxe_menu_data():
			return self.__return(
				f"Error: Either {self.__image_json_file} does not exist, or unable to parse {self.__image_json_file}",
				500
			)

		# Check if menu data changed — if so, regenerate and cache
		if old_data != self.__ipxe_menu_data:
			self.__ipxe_cache_1 = self.__generate_ipxe_script(1)
			self.__ipxe_cache_2 = self.__generate_ipxe_script(2)
			self.__last_updated = datetime.utcnow().isoformat()


		type = request.args.get("type", False)
		if not type or type == '1':
			ipxe_cache = self.__ipxe_cache_2 # sanboot is less of a headache than memdisk
		elif type == '2':
			ipxe_cache = self.__ipxe_cache_1
		else:
			 return self.__return(
				f"Error: Allowed types are 1 or 2",
				400
			)

		return self.__return(
			ipxe_cache,
			False,
			{"X-Last-Updated": self.__last_updated or "never"}
		)

	# Get a file
	def __get_file(self, filename):
		safe_filename = secure_filename(filename)
		return send_from_directory(self.__mount_dir, safe_filename, as_attachment=True)

	# Start the Web Server using waitress
	def start_web_app(self):
		# Waitress
		serve(self.__app, host=self.__host, port=self.__port, ident=self.__server_header)

		# Flask (For debugging)
		#self.__app.run(debug=True, host=self.__host, port=self.__port)