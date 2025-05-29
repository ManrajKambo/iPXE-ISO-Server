from iPXE import iPXE

def main():
	ipxe = iPXE(
		host = "0.0.0.0",
		port = 80,
		serverHeader = "iPXE",
		mountDir = "/mount",
		filesDir = "files",
		imageJsonFile = "/Images.json"
	)
	ipxe.start_web_app()

if __name__ == "__main__":
	main()