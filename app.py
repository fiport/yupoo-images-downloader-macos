import os
import sys
os.environ['PYTHONASYNCIODEBUG'] = '1'

CONFIG_PATH = os.path.dirname(__file__).replace("\\", "/")+"/config.json"
import asyncio
from time import sleep, perf_counter
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
import rich.prompt as prompt
import re
from tkinter import filedialog
import tkinter as tk
import json
import requests

from edit_rich import make_prompt, render_default

clear = lambda: os.system("cls" if os.name == 'nt' else "clear")
clear()

class App():
	def __init__(self):
		self.version = '1.0.0'
		self.update_message = None

		self.console = Console(color_system="auto")

	def main(self):
		self.default()
		self.console.print("\nPrograma desenvolvido para te ajudar a baixar \nimagens com qualidade e facilmente do site da [#0ba162]Yupoo[/]!")
		self.console.print("\n[b #6149ab]Opções[/]")
		self.console.print("[b #baa6ff]1.[/] Baixe todas as imagens de todos os álbuns. ([bold u #c7383f]pesado[/])")
		self.console.print("[b #baa6ff]2.[/] Baixe apenas a foto principal de todos álbuns.")
		self.console.print("[b #baa6ff]3.[/] Inserir álbuns ou categorias para baixar todas as fotos.")
		self.console.print("[b #baa6ff]4.[/] Inserir álbuns ou categorias para baixar apenas a foto principal.")

		self.edit_rich()
		self.opt = prompt.Prompt.ask("\n[b #6149ab]>>[/]  Selecione uma opção", choices=["1", "2", "3", "4"], default="3")
		clear()
		self.default()
		try:
			self.execute_answer()
		except Exception as e:
			self.console.print(f"\n[b #c7383f]{e}[/]")
			import traceback
			with open("info.log", "a") as f:
				f.write(f'albums: {self.yupoo_downloader.albums}\n\n{traceback.format_exc()}\n-\n')
			return
		self.console.print(f"\n[b #0ba162]Concluído! Imagens salvas no diretório {self.path_to_save}, na pasta chamada fotos_yupoo.[/]")
		self.console.print(f"Tempo gasto: [b #0ba162]{round(perf_counter()-self.start_time, 2)}[/]")

		import platform
		import subprocess

		def explore(path):
			# explorer would choke on forward slashes
			path = os.path.normpath(path)

			if os.path.isdir(path):
					subprocess.run(['open', path])
			elif os.path.isfile(path):
					subprocess.run(['open', '-R,', path])

		explore(self.path_to_save+"/fotos_yupoo")

		opt = prompt.Confirm.ask("\nDeseja executar o programa novamente?", default=True)
		if opt:
			os.execl(sys.executable, sys.executable, *sys.argv)
		else:
			sys.exit()

	def execute_answer(self):
		try:
			selected_print = lambda option, text: self.console.print(f"\nOpção [b #6149ab]{option}[/] selecionada: [b #baa6ff]{text}[/]")\
			
			def choose_path():
				self.console.print("\nEscolha o [#baa6ff b]diretório padrão[/] para salvar as fotos.")
				root = tk.Tk()
				root.withdraw()
				while True:
					self.path_to_save = filedialog.askdirectory()
					if self.path_to_save != "":
						break
				with open("config.json", "w") as f:
					config = {'path_to_save': self.path_to_save}
					json.dump(config, f)

			if os.path.exists(CONFIG_PATH):
				with open("config.json", "r") as f:
					config = json.load(f)
					self.path_to_save = config['path_to_save']
				if self.path_to_save != "":
					self.console.print(f"\nDiretório padrão: [b #baa6ff]{self.path_to_save}[/]")
					opt = prompt.Confirm.ask("O diretório para salvar as fotos está correto?", default=True)
					if opt == False:
						choose_path()
				else:
					choose_path()
			else:
				choose_path()
			
			clear()
			from main import YupooDownloader
			self.default()
			if self.opt == "1" or self.opt == "2":
				if self.opt == "1":
					selected_print_ = lambda: selected_print("1", "Baixando todas as fotos do catálogo!")
					selected_print_()
					self.console.print("\nInsira o link do catálogo.")
					while True:
						url = prompt.Prompt.ask("[#6149ab b]link[/]")
						url = self.verify_url(self.parse_url(url))
						if url != None:
							break
					clear()
					self.default()
					selected_print_()
					self.start_time = perf_counter()
					self.yupoo_downloader = YupooDownloader(all_albums=True, urls=url, cover=False)
					asyncio.run(self.yupoo_downloader.main())
				else:
					selected_print_ = lambda: selected_print("2", "Baixando todas as fotos principais do catálogo!")
					selected_print_()
					self.console.print("\nInsira o link do catálogo.")
					while True:
						url = prompt.Prompt.ask("[#6149ab b]link[/]")
						url = self.verify_url(self.parse_url(url))
						if url != None:
							break
					clear()
					self.default()
					selected_print_()
					self.start_time = perf_counter()
					self.yupoo_downloader = YupooDownloader(all_albums=True, urls=url, cover=True)
					asyncio.run(self.yupoo_downloader.main())
			elif self.opt == "3" or self.opt == "4":
				if self.opt == "3":
					selected_print_ = lambda: selected_print("3", "Baixando todas as fotos dos álbuns selecionados!")
					selected_print_()
				else:
					selected_print_ = lambda: selected_print("4", "Baixando todas as fotos principais dos álbuns selecionados!")
					selected_print_()
				self.console.print("\nInsira os links dos álbuns para download.")
				self.console.print("([#baa6ff]digite [#0ba162 b]ok[/] para executar e [#c7383f b]del[/] para cancelar o último link inserido[/])\n")
				self.urls = []
				while True:
					url = prompt.Prompt.ask("[#6149ab b]link[/]")
					url = url
					if url == "ok":
						if len(self.urls) != 0:
							break
						self.console.print(f'[b #c7383f]insira pelo menos um link antes de iniciar![/]\n')
					elif url == "del":
						if len(self.urls) != 0:
							self.urls.pop()
							self.console.print(f'último link [#c7383f]removido[/]!\n')
						else:
							self.console.print(f'[b #c7383f]insira pelo menos um link antes de remover![/]\n')
					else:
						self.verify_url(self.parse_url(url))
				if self.opt == "3":
					clear()
					self.default()
					selected_print_()
					self.start_time = perf_counter()
					self.yupoo_downloader = YupooDownloader(all_albums=False, urls=self.urls, cover=False)
					asyncio.run(self.yupoo_downloader.main())
				else:
					clear()
					self.default()
					selected_print_()
					self.start_time = perf_counter()
					self.yupoo_downloader = YupooDownloader(all_albums=False, urls=self.urls, cover=True)
					asyncio.run(self.yupoo_downloader.main())
		except Exception as e:
			raise Exception(e)

	def parse_url(self, url):
		rx_url = lambda text: re.findall(r'(?<=https:\/\/)(.*?)(?=\.x)', text)
		if len(rx_url(url)) == 0:
			rx_catalog = re.findall(r'(?<=photos\/)(.*?)(?=\/)', url)
			if len(rx_catalog) != 0:
				catalog = rx_catalog[0]
				url_split = [part for part in url.split('/') if part != '']

				if url_split[-1] == 'albums' and url_split[-2] == catalog: # catalog url
					url = f'https://{catalog}.x.yupoo.com/'
				elif url_split[-2] == 'albums' and url_split[-3] == catalog: # album url
					url = f'https://{catalog}.x.yupoo.com/albums/{url_split[-1]}'
				elif url_split[-2] == 'categories' or url_split[-2] == 'collections' and url_split[-3] == catalog: # catalog id url
					url = f'https://{catalog}.x.yupoo.com/categories/{url_split[-1]}'
				else:
					return None
		return url

	def verify_url(self, url):
		if url == None:
			self.console.print(f'[b #c7383f]ultimo link não considerado, link inválido!\n')
		elif "yupoo" not in url:
			self.console.print(f'[b #c7383f]ultimo link não considerado, link inválido!\nlembre-se de inserir apenas catálogos do site Yupoo![/]\n')
		elif "https://" != url[0:8]:
			self.console.print(f'[b #c7383f]ultimo link não considerado, link inválido!\nlembre-se de colocar "https://"[/]\n')
		else:
			if self.opt == "1" or self.opt == "2":
				if "categories" in url or "collections" in url:
					self.console.print(f'[b #c7383f]ultimo link não considerado, link inválido!\nuse a 3 ou 4 opção para baixar categorias[/]\n')
				elif ".com" not in url[-5:]:
					self.console.print(f'[b #c7383f]ultimo link não considerado, link inválido!\nnão pode haver nada após ".com", exemplo de link válido: "https://_____.x.yupoo.com/"[/]\n')
				else:
					return url
			elif self.opt == "3" or self.opt == "4":
				if url not in self.urls:
					self.urls.append(url)

	def default(self):
		if self.update_message:
			self.console.print(Panel.fit(self.update_message, title="[blink #4912ff]AVISO[/]", subtitle="[blink #4912ff]AVISO[/]"))

		self.console.print(f"[#baa6ff]Aplicação [#6149ab b]v{self.version}[/], desenvolvida por [#6149ab b]Filipe Port[/]![/]\n")
		self.console.print(Panel.fit("[#ffffff]Considere apoiar o [bold #4912ff]PROJETO[/][/]!\n[#ffffff]Chave [bold u #0ba162]PIX[/]: [bold #00ff73](49) 9 99117-0701[/]", title="[blink #4912ff]***[/]", subtitle="[blink #4912ff]***[/]"))

	def edit_rich(self):
		def choices_style(style='prompt.choices'):
			prompt.PromptBase.make_prompt = make_prompt(style=style, DefaultType=prompt.DefaultType, Text=Text)
		def default_style(style='prompt.default', path="Confirm"):
			if path == "Confirm":
				prompt.Confirm.render_default = render_default(path=path, style=style,DefaultType=prompt.DefaultType, Text=Text)
			elif path == "Prompt":
				prompt.PromptBase.render_default = render_default(path=path,style=style,DefaultType=prompt.DefaultType, Text=Text)

		prompt.Confirm.choices = ['s', 'n']
		prompt.Confirm.validate_error_message = 'Digite apenas [bold #0ba162]S[/] e [bold #c7383f]N[/]\n'
		prompt.PromptBase.illegal_choice_message = '[#c7383f]Por favor, selecione uma das opções disponíveis'
		choices_style('bold #baa6ff')
		default_style('bold #6149ab')
		default_style('bold #6149ab', 'Prompt')
try:
	clear()
	app = App().main()
	while True:
		sleep(1)
except KeyboardInterrupt:
	clear()
	app = None
	clear()