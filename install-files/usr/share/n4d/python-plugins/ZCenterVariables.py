import time
import copy

class ZCenterVariables:
	
	NOT_CONFIGURED=0
	CONFIGURED=1
	FAILED=-1
	
	DAY=60*60*24
	#DAY=1
	
	def __init__(self):
		
		pass
		
	#def init
	
	def startup(self,options):
		
		self.n4d_vars=objects["VariablesManager"]
		
		self.internal_variable=copy.deepcopy(objects["VariablesManager"].get_variable("ZEROCENTERINTERNAL"))
		self.variable=copy.deepcopy(objects["VariablesManager"].get_variable("ZEROCENTER"))
		
		
		
		if self.internal_variable==None:
			try:
				self.n4d_vars.add_variable("ZEROCENTERINTERNAL",{},"","ZeroCenter internal variable","zero-center")
				self.internal_variable={}
			except Exception as e:
				
				self.internal_variable=self.n4d_vars.get_variable("ZEROCENTERINTERNAL")
		
		if self.variable==None:
			try:
				self.n4d_vars.add_variable("ZEROCENTER",{},"","ZeroCenter states variable","zero-center")
			except:
				pass
			self.variable={}
		
	#def init
	
	def set_zc_message(self,app,message,message_es="",message_qcv=""):
		
		try:
			if "messages" not in self.internal_variable:
				self.internal_variable["messages"]={}
			self.internal_variable["messages"][app]={}
			self.internal_variable["messages"][app]["date"]=time.time()
			self.internal_variable["messages"][app]["message"]={}
			self.internal_variable["messages"][app]["message"]["en"]=message
			self.internal_variable["messages"][app]["message"]["es"]=message_es
			self.internal_variable["messages"][app]["message"]["qcv"]=message_qcv
			self.internal_variable["messages"][app]["message"]["ca"]=message_qcv
			self.n4d_vars.set_variable("ZEROCENTERINTERNAL",copy.deepcopy(self.internal_variable))
			return True
			
		except Exception as e:
			print(e)
			return False
			
		
	#def set_zc_message
	
	def remove_zc_message(self,app):
		
		if app  in self.internal_variable["messages"]:
			self.internal_variable["messages"].pop(app)
	
		return True
		
	#def remove_zc_message
	
	def get_zc_messages(self,lang="en",date_filter=None):
		
		if date_filter==None or type(date_filter)!=type(0):
			date_filter=time.time()-self.DAY*30
			
		ret=""
		t=time.time()
		
		try:
			for app in sorted(self.internal_variable["messages"].keys()):
				
				if date_filter < self.internal_variable["messages"][app]["date"] :
					
					try:
						ret+="          ["+app+"] " + self.internal_variable["messages"][app]["message"][lang]+"          "
					except:
						try:
							ret+="          ["+app+"] " + self.internal_variable["messages"][app]["message"]["en"]+"          "
						except:
							pass
							
			ret=ret.rstrip(" ").lstrip(" ")
			return ret
			
		except Exception as e:
			return ""
			
	#def get_zc_messages
	
	def get_current_time(self):
		return time.strftime("%d/%m/%Y",time.localtime())
	
	def get_state(self,app,full=False):
		
		if full:
			return self.get_full_info(app)
			
		if app in self.variable:
			if "state" in self.variable[app]:
				return self.variable[app]["state"]
			else:
				return ZCenterVariables.NOT_CONFIGURED
		else:
			return ZCenterVariables.NOT_CONFIGURED
			
	#def get_state
			
	def get_full_info(self,app):
		
		if app in self.variable:
			return self.variable[app]
		else:
			return {"state":ZCenterVariables.NOT_CONFIGURED,"time":self.get_current_time()}
			
	#def get_full_info
	
	def set_custom_state(self,app,state):

		try:
			if app not in self.variable:
				self.variable[app]={}
				
			self.variable[app]["state"]=state
			self.variable[app]["time"]=self.get_current_time()
			
			self.n4d_vars.set_variable("ZEROCENTER",copy.deepcopy(self.variable))
			return True
		except:
			return False

	#def set_state
	
	def set_configured(self,app):
		
		return self.set_custom_state(app,ZCenterVariables.CONFIGURED)
		
	def set_non_configured(self,app):
		
		return self.set_custom_state(app,ZCenterVariables.NOT_CONFIGURED)
		
	def set_failed(self,app):
		
		return self.set_custom_state(app,ZCenterVariables.FAILED)
		
	def set_custom_text(self,app,text):
		
		try:
			if not app in self.variable:
				self.variable[app]={}
			self.variable[app]["custom_text"]=text
			self.n4d_vars.set_variable("ZEROCENTER",copy.deepcopy(self.variable))
			
			return True
		
		except Exception as e:
			print e
			return False
		
	#def set_custom_text
	
	def add_pulsating_color(self,app):
		
		try:
			if not app in self.variable:
				self.variable[app]={}
				
			self.variable[app]["pulsating"]=True
			self.n4d_vars.set_variable("ZEROCENTER",copy.deepcopy(self.variable))
		
		except Exception as e:
			print e
			return False
		
	#def add_pulsating_color
	
	def remove_pulsating_color(self,app):
		
		try:
			if not app in self.variable:
				self.variable[app]={}
				
			self.variable[app]["pulsating"]=False
			self.n4d_vars.set_variable("ZEROCENTER",copy.deepcopy(self.variable))
		
		except Exception as e:
			print e
			return False
		
	#def remove_pulsating_color
	
	def get_all_states(self):
		
		return self.variable
		
	#def get_all_states
	
	
#class ZCenterVariables
