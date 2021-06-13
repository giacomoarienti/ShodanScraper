from sys import stdout

class StatusBar(object):
	def __init__(self, total:int, toolbar_width=40) -> None:
		self.toolbar_width = toolbar_width
		
		self.total = total

		self.percentage = 0
		self.bar_progress = 0

	def draw(self) -> None:
		stdout.write('\r')
		stdout.write("Progress: [" +  ("=" * self.bar_progress) + ">" + (" " * (self.toolbar_width - self.bar_progress)) + "] " + str(self.percentage) + "%")
		stdout.flush()
		
	def update(self, bar_progress: int) -> None:
		self.percentage = int(round(bar_progress / self.total, 2) * 100)
		
		self.bar_progress = int(self.toolbar_width * self.percentage / 100)
		self.draw()
