import aiohttp
import aiofiles
import yarl
import json
import ujson
import re
import asyncio
import urllib
import traceback

from random import randint
from bs4 import BeautifulSoup
from aiohttp_socks import ProxyConnector

class MoodleCli:
	def __init__(self,username,password,moodle,repoid,session):
		self.username = username
		self.password = password
		self.moodle = moodle
		self.session = session
		self.repoid = repoid
		self.tokens = []
		self.tokens2 = []
	
	async def login(self):
		url = f"{self.moodle}/login/index.php"
		async with self.session.get(url,ssl=False) as resp:
			text = await resp.text()
			soup = BeautifulSoup(text,"html.parser")
			try:
				token = soup.find("input", attrs={"name": "logintoken"})["value"]
			except:
				strtext = '<input type="hidden" name="logintoken" value="\w{32}">'
				token = re.findall(strtext, text)
				token = re.findall("\w{32}", token[0])[0]
			payload = {"anchor":"","logintoken":token,"username":self.username,"password":self.password}
		
		async with self.session.post(url,data=payload,ssl=False) as response:
			text2 = await response.text()
			soup2 = BeautifulSoup(text2,"html.parser")
			try:
				userid = soup2.find('div',{'id':'nav-notification-popover-container'})['data-userid']
				self.tokens.append(str(userid))
			except:
				userid = re.findall('(?<=userid=")(.*?)(?=")', userid)[-1]
				self.tokens.append(str(userid))
			try:
				sesskey = soup.find("input",attrs={"name":"sesskey"})["value"]
				self.tokens2.append(sesskey)
			except:
				sesskey = re.findall('(?<="sesskey":")(.*?)(?=")', text2)[-1]
				self.tokens2.append(sesskey)
			
			if "loginerrors" in text2:
				return False
			else:
				return True
		
	async def upload(self,f):
		url = f"{self.moodle}/user/edit.php?id={self.tokens[-1]}&returnto=profile"
		async with self.session.get(url,ssl=False) as resp:
			text = await resp.text()
			soup = BeautifulSoup(text,"html.parser")
			try:
				clientid = str(soup.find('div',{'class':'filemanager'})['id']).replace('filemanager-','')
			except:
				strtext = '"client_id":"\w{13}"'
				clientid = re.findall(strtext, text)
				clientid = re.findall("\w{13}", clientid[0])[0]
				
			query = yarl.URL((soup.find('object',attrs={'type':'text/html'})['data'])).query
			
			fi = open(f,"rb")
			bytes = query["areamaxbytes"]
			if bytes == "0":
				bytes = "-1"
				
			dict = {"author":"Kill",
			           "license":"allrightsreserved",
			           "itemid":query["itemid"],
			           "repo_id":str(self.repoid),
			           "env":query["env"],
			           "sesskey":query["sesskey"],
			           "client_id":clientid,
			           "maxbytes":query["maxbytes"],
			           "areamaxbytes":bytes,
			           "ctx_id":query["ctx_id"]}
			payload = {"repo_upload_file":fi, **dict}
			url2 = f"{self.moodle}/repository/repository_ajax.php?action=upload"
			async with self.session.post(url2,data=payload,ssl=False) as response:
				text2 = await response.text()
				try:
					jsonurl = ujson.loads(text2)["url"]
				except:
					jsonurl = json.loads(text2)["url"]
		return jsonurl
	
	async def linkcalendar(self,urls):
		try:
			url = f"{self.moodle}/lib/ajax/service.php?sesskey={self.tokens2[-1]}&info=core_calendar_submit_create_update_form"
			payload = [{"index":0,"methodname":"core_calendar_submit_create_update_form","args":{"formdata":"id=0&userid={}&modulename=&instance=0&visible=1&eventtype=user&sesskey={}&_qf__core_calendar_local_event_forms_create=1&mform_showmore_id_general=1&name=Evento&timestart[day]=4&timestart[month]=4&timestart[year]=2022&timestart[hour]=18&timestart[minute]=55&description[text]={}&description[format]=1&description[itemid]={}&location=&duration=0"}}]
			urlin = '<p dir="ltr"><span style="font-size: 14.25px;">{}</span></p>'
			urlparse = urllib.parse.quote_plus(urlin.format(urls))
			payload[0]["args"]["formdata"] = payload[0]["args"]["formdata"].format(self.tokens[-1],self.tokens2[-1],urlparse,randint(1000000000, 9999999999))
			async with self.session.post(url,data=json.dumps(payload),ssl=False) as resp:
				resptext = await resp.json()
				resptext = resptext[0]["data"]["event"]["description"]
			return re.findall("https?://[^\s\<\>]+[a-zA-z0-9]",resptext)[-1]
		except Exception as exc:
			print(traceback.format_exc())
			return None