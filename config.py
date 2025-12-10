######################
api_id = 19961504
api_hash = "28de3a8f4b68b388bfe47bf84d1b124b"
bot_token = "5361532937:AAHar232-6BrUv11jxemQmZbeytcxI5GOeI"

users = {}

######################
OWNER = "anonedev"

def makeuser(usern):
	users[usern] = {"user":"__Sin Definir__",
	                "passw":"__Sin Definir__",
	                "host":"__Sin Definir__",
	                "repoid":"__Sin Definir__",
	                "zips":"__Sin Definir__",
	                "proxy":"__Desactivado❌__"}

def getusern(user):
	try:
		return users[user]
	except:
		return None

def outusern(usern):
	try:
		del users[usern]
	except:
		return None

def savedata(usern,data):
	users[usern] = data