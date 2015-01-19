import json
import threading
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer

import variables, notification, call

import xbmc
import xbmcaddon

__addon__					= xbmcaddon.Addon(id=variables.__addon_id__)

__notification_posted__		= '/notification/posted'
__notification_removed__	= '/notification/removed'

__call_start__				= '/call/started'
__call_ended__				= '/call/ended'
__call_missed__				= '/call/missed'

SAVED_VOLUME_LEVEL = 0

class PostHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.end_headers()
		self.send_response(404)

	def do_POST(self):
		self.end_headers()

		if not self.is_authorized():
			self.send_response(401)
			return

		content_length = int(self.headers['Content-Length'])
		data = self.rfile.read(content_length)

		if self.path == __notification_posted__:
			self.__on_notification_posted(data)

		elif self.path == __notification_removed__:
			self.__on_notification_removed(data)

		elif self.path == __call_start__:
			self.__on_call_started(data)

		elif self.path == __call_ended__:
			self.__on_call_ended(data)

		elif self.path == __call_missed__:
			self.__on_call_missed(data)

		else:
			self.send_response(404)

	def is_authorized(self):
		is_auth_enabled = __addon__.getSetting('base_auth_enabled')
		username = __addon__.getSetting('username')
		password = __addon__.getSetting('password')

		if 'Authorization' in self.headers:
			auth = self.headers['Authorization'].split()[1].decode('base64')
			user = auth.split(':')[0]
			pwd = auth.split(':')[1]

			if is_auth_enabled:
				if user == username and pwd == password:
					return True
				else:
					return False
			else:
				return True
		else:
			return is_auth_enabled

	def __on_notification_posted(self, data):
		data = json.loads(data)

		notification.post_notification(data['id'], data['appName'], data['title'], data['text'], data['bigText'],
									  data['infoText'], data['tickerText'], data['subText'], data['displayTime'],
									  data['largeIcon'], data['appIcon'], data['smallIcon'])

	def __on_notification_removed(self, data):
		pass

	def __on_call_started(self, data):
		global SAVED_VOLUME_LEVEL
		SAVED_VOLUME_LEVEL = call.on_call_start(data)

	def __on_call_ended(self, data):
		call.on_call_end(data, SAVED_VOLUME_LEVEL)

	def __on_call_missed(self, data):
		call.on_call_end(data, SAVED_VOLUME_LEVEL)


if __name__ == '__main__':
	ip = xbmc.getIPAddress()
	port = int(__addon__.getSetting(variables.__setting_key_port__))
	server = HTTPServer((ip, port), PostHandler)

	threading.Thread(target=server.serve_forever).start()

	monitor = xbmc.Monitor()
	while True:
		if monitor.waitForAbort(5):
			server.socket.close()
			break