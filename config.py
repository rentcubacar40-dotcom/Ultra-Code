######################
api_id = 20534584
api_hash = "6d5b13261d2c92a9a00afc1fd613b9df"
bot_token = "8181002237:AAFNWamFKqGI9dHXSEpzAxTNmUc0bz6S0Sc"

users = {}

######################
OWNER = "Eliel_21"

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
