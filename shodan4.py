import time
import json
import random
import re
import threading
import statusbar

class ShodanScraper(object):
	VERSION = "4.2"
	OFILE = "shodan_output.txt"

	USER_AGENTS = ["Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Safari/537.36", "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", "Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1 (compatible; AdsBot-Google-Mobile; +http://www.google.com/mobile/adsbot.html)", "Mozilla/5.0 (Linux; Android 5.0; SM-G920A) AppleWebKit (KHTML, like Gecko) Chrome Mobile Safari (compatible; AdsBot-Google-Mobile; +http://www.google.com/mobile/adsbot.html)", "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3599.0 Safari/537.36", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.18247", "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; rv:11.0) like Gecko", "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3599.0 Safari/537.36", "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3599.0 Safari/537.36", "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko", "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3599.0 Safari/537.36", "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3599.0 Safari/537.36", "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3599.0 Safari/537.36", "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"]
	IP_REGEX = "^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$}"

	BAR_PROGRESS = 0

	THREADS = []

	def __init__(self, settings_file="") -> None:
		self.settings_file = settings_file

		self.delay = 0
		self.api_key = ""
		self.resultsn = 0 
		self.search = ""
		self.port = 0
		self.country = ""
		self.org = ""

		self.pages = 0
		self.status_bar = None
		self.shodan = None

		self.query = ""

		self.load_settings()

	def load_settings(self):
		f = None
		try:
			f = open(self.settings_file, 'r')
		except FileNotFoundError:
			print(f"Error: failed to open {self.settings_file}")
			exit(-1)

		try:
			data = json.load(f)
		except:
			print(f"Error: failed to parse {self.settings_file}")
			exit(-1)

		f.close()

		try:
			self.delay = data['delay'] 
			self.api_key = data['api'] 
			self.resultsn = data['results'] 
			self.search = data['search'] 
			self.port = data['port'] 
			self.country = data['country'] 
			self.org = data['org']
		except:
			print(f"Error: failed to load settings from {self.settings_file}")
			exit(-1)

		
		if(self.api_key == "" or self.api_key == None or self.api_key == "API"):
			print("Error: you haven't set the API key")
			exit(-1)

		if(self.resultsn == None or self.resultsn == 0):
			print("Error: you haven't set the number of results")
			exit(-1)

		if(self.resultsn < 100):
			print("Error: results must be at least 100")
			exit(-1)

		if(self.search == "" or self.search == None):
			print("Error: search query cannot be empty")
			exit(-1)

	def check_dependencies(self) -> None:
		try:
			import shodan, requests
		except ImportError:
			print("Error: missing modules")
			print("pip3 install -r requirements.txt")
			exit(-1)
	
	def test_api(self) -> int:
		import requests

		url = "https://api.shodan.io/api-info?key=" + self.api_key
		headers = {
			'Accept': '*/*',
			'User-Agent': random.choice(self.USER_AGENTS)
		}
	
		r = requests.get(url, headers=headers)
		if(r.status_code == 403 or r.status_code == 401):
			print("Error: invalid API")
			exit(-1)
		
		json_data = ""
		try:
			json_data = json.loads(r.text)
		except:
			print("Error: failed to parse api response")
			exit(-1)
		
		for i in json_data:
			if(i == "error"):
				print("Error: your api is rate limited")
				exit(-1)
			if(i == "query_credits"):
				credits = int(json_data["query_credits"])
				if(credits <= 0 or credits < self.pages):
					print("Error: not enought credits")
					exit(-1)
				else:
					print(f"Credits: {str(credits)}\n")
					return

	def build_search_query(self) -> None:
		q = self.search
		if(self.country != ""):
			q += ' country:"' + self.country + '"'
		if(self.port > 0):
			q += ' port:"' + str(self.port) + '"'
		if(self.org != ""):
			q += ' org:"' + self.org + '"' 
		self.query = q

	def display_message(self) -> None:
		print(f"ShodanScraper v{self.VERSION}:\nStarting scraping...\n")

	def check_query(self) -> None:
		results = self.shodan.search(self.query)
		if(results == 0):
			print("Error: failed to find any result")
			exit(-1)
		if(self.resultsn > results['total']):
			self.resultsn = results['total']

		print(f'Results found: {self.resultsn}')

	def init_shodan(self) -> None:
		import shodan
		self.shodan = shodan.Shodan(self.api_key)

	def init_status_bar(self) -> None:
		self.pages = self.resultsn // 100 + 1
		self.status_bar = statusbar.StatusBar(total=self.pages)

	def ip_scarpe(self, page) -> None:
		while True:
			time.sleep(self.delay)

			try:
				results = self.shodan.search(self.query, page=page)
				for result in results['matches']:
					with open(self.OFILE, "a") as f:
						f.write(result['ip_str'] + "\n")
				return
			except:
				time.sleep(self.delay)
				continue

	def start_threads(self) -> None:
		for p in range(self.pages):
			t = threading.Thread(target=self.ip_scarpe, args=(p,))
			t.start()
			self.THREADS.append(t)

			time.sleep(0.01)

		for t in self.THREADS:
			t.join()
			self.BAR_PROGRESS += 1
			self.status_bar.update(self.BAR_PROGRESS)

	def clean_data(self) -> None:		
		with open(self.OFILE, "r") as f:
			lines = set(f.readlines())
		with open(self.OFILE, "w") as f:
			for line in lines:
				if(re.search(self.IP_REGEX, line)):
					f.write(line)

		print("\n\nScraping done")

	def start(self) -> None:
		self.check_dependencies()

		self.test_api()

		self.build_search_query()

		self.display_message()

		self.init_shodan()

		self.check_query()

		self.init_status_bar()

		self.start_threads()

		self.clean_data()

		self.THREADS = []


ShodanScraper(
	settings_file="shodan_settings.json"
).start()