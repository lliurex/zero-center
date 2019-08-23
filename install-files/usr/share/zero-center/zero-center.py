#!/usr/bin/env python
# -*- coding: utf-8 -*
 

import os
import multiprocessing
import time
import random
import xmlrpclib
import cairo
import grp
import sys
import subprocess
import json

try:
	#if ("XDG_SESSION_TYPE" in os.environ and os.environ["XDG_SESSION_TYPE"]=="x11") or ("SSH_CLIENT" in os.environ and os.environ["SSH_CLIENT"]!=""):
	if True:
		import gi
		gi.require_version('Gtk', '3.0')
		gi.require_version('PangoCairo', '1.0')
		from gi.repository import Gtk, Gdk, GObject, GLib, PangoCairo, Pango
except Exception as e:
	pass
	#print e
	#zero-server-wizard initialization forces me to do this

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import gettext
gettext.textdomain('zero-center')
_ = gettext.gettext


BAR_HEIGHT=90
CONF_X=5

if os.path.exists("/home/lliurex/banners/"):
	BANNER_PATH="/home/lliurex/banners/"
else:
	BANNER_PATH="/usr/share/banners/lliurex-neu/"
	

class CategoriesParser:
	
	CATEGORIES_PATH="/usr/share/zero-center/categories/"
	
	def __init__(self):
		
		self.parse_categories()
		
	#def init
	
	def parse_categories(self,path=None):
		
		self.categories=[]
		
		if path==None:
			path=self.CATEGORIES_PATH
			
		for item in os.listdir(path):
			file_path=path+item
			
			f=open(file_path)
			lines=f.readlines()
			f.close()
			
			cat={}
			
			for line in lines:
				key,value=line.split("=")
				cat[key]=value.strip("\n")
				if key=="level":
					cat[key]=int(cat[key])
			
			self.categories.append(cat)
			
		tmp=[]
		
		while len(self.categories)>0:
			selected_index=0
			index=0
			level=0
			for item in self.categories:
				if item["level"]>level:
					level=item["level"]
					selected_index=index
					
				
				index+=1
			
			tmp.append(self.categories[selected_index])
			self.categories.pop(selected_index)
			
		self.categories=tmp
		
	#def parse_categories
		
		
#class CategoriesParser


class AppParser:
	
	BASE_DIR="/usr/share/zero-center/"
	APP_PATH=BASE_DIR+"applications/"
	ZMD_PATH=BASE_DIR+"zmds/"
	
	
	def __init__(self):
		
		self.categories=["ID","Name","Comment","Icon","Category","Icon","ScriptPath","Groups","Service","Locks"]
		self.apps={}
		self.app_list=[]
		self.configured=[]
		#print("[ZeroCenter] Parsing apps...")
		self.parse_all()
		
	#def init

	
	def add_app(self,app):
		
		try:
			if app["Category"].lower() not in self.apps:
				self.apps[app["Category"].lower()]=[]
			
			self.apps[app["Category"].lower()].append(app)
			self.app_list.append(app["ID"])
		except:
			pass
			
	#def add_app
	
	def parse_all(self,dir=None):
		
		if dir==None:
			dir=self.APP_PATH
	
		for item in os.listdir(dir):
			file_path=self.APP_PATH+item
			app=self.parse_file(file_path)
			self.add_app(app)
			
	#def parse_all

	
	def parse_file(self,file_path):
		
		f=open(file_path)
		lines=f.readlines()
		f.close()
		id=file_path.split("/")[-1].split(".")[0]
		app={}
		for item in lines:
			try:
				key,value=item.split("=")
				app[key]=value.strip("\n")
			except:
				pass
		
		app["ID"]=id
		app["configured"]=-1
		app["custom_msg"]=""
		
		app["bar_height"]=BAR_HEIGHT
		app["conf_alpha"]=1.0

		
		app["expanding"]=False
		app["restoring"]=False

		return app
		
	#def parse_file

	
#class AppParser


class ZeroCenter:
	
	def __init__(self):
		
		self.client=xmlrpclib.ServerProxy("https://localhost:9779")
		self.create_user_env()
		self.categories_parser=CategoriesParser()
		self.app_parser=AppParser()
		self.configured_apps=[]
		self.get_states()
		
		self.mprocess=multiprocessing.Process()
		self.commands=["set-configured","set-non-configured","set-failed","set-custom-text","add-zero-center-notification","remove-zero-center-notification","help","add-pulsating-color","remove-pulsating-color","non-animated","animated"]
		self.drawing_mode=True
		self.msg_text=""
		self.msg_x=0
		self.scrolling=False
		
		try:
			self.msg_text=self.client.get_zc_messages("","ZCenterVariables",self.lang)
			if self.msg_text=="":
				txt=self.client.lliurex_version("","LliurexVersion")
				if type(txt)==type([]):
					self.msg_text=str(txt[1])
				else:
					f=open("/etc/lsb-release")
					lines=f.readlines()
					f.close()
					for line in lines:
						if "DISTRIB_DESCRIPTION" in line:
							self.msg_text=line.split("=")[1]
			#Load slave_blacklist
			self.blacklist=self.client.get_variable("","VariablesManager","SLAVE_BLACKLIST")

		except:
			self.msg_text=""
		
		#self.msg_text="hi, i'm a long enough text so that it won't show in just one line. I wonder how many lines I can get inside the box. In my restless dreams I see that town, Silent Hill. I don't know what to type, but I have to keep typing"
		#57
		
	#def init

	
	def get_states(self):
		
		try:
			var=self.client.get_all_states("","ZCenterVariables")
		except:
			local_path="/var/lib/n4d/variables-dir/ZEROCENTER"
			if os.path.exists(local_path):
				f=open(local_path)
				var=json.load(f)["ZEROCENTER"]["value"]
				f.close()
			else:
				var={}
				
		try:
			for cat in self.app_parser.apps:
			
				for app in self.app_parser.apps[cat]:
					app["configured"]=0
					
					if app["ID"] in var:
						for key in ["state","pulsating","time","custom_text"]:
							if key in var[app["ID"]]:
								app[key]=var[app["ID"]][key]
		
							
					if "state" in app:
						app["configured"]=app["state"]
				
					if app["configured"]==1:
						self.configured_apps.append(app["ID"])
				
				
		except Exception as e:
			print(e)
			pass
			
	#def get_states

	
	def get_translation(self,text):
		
		for category in self.categories_parser.categories:
			
			if text.lower()==category["name"].lower():
				for lang in self.language:
					try:
						return category["name["+lang+"]"]
					except Exception as e:
						pass
				return category["name"]
		
		return text
		
	#def get_translation

	
	def get_name(self,app):
		
		for lang in self.language:
			try:
				return app["Name["+lang+"]"]
			except:
				pass
				
		return app["Name"]
		
	#def get_name

	
	def get_comment(self,app):
		
		for lang in self.language:
			try:
				return app["Comment["+lang+"]"]
			except:
				pass
				
		return app["Comment"]
		
	#def get_name

	
	def create_user_env(self):
		
		def fallback_lang():
			
			try:
				self.lang=os.environ["LANG"].replace(".UTF-8","")
				self.lang=self.lang.replace(".utf8","")
				self.language=[]
				self.language.append(self.lang)
				self.lang=self.lang.split("_")[0]
				if "es_ES" in self.language and "es" not in self.language:
					self.language.insert(self.language.index("es_ES")+1,"es")
				if "ca_ES@valencia" in self.language or "ca@valencia" in self.language:
					self.language.insert(self.language.index("ca_ES@valencia"),"qcv")
				
			except:
				self.lang="en"
				self.language=["en"]
		
		try:
			self.lang=os.environ["LANGUAGE"].replace(".UTF-8","").split(":")[0]
			self.language=os.environ["LANGUAGE"].replace(".UTF-8","").split(":")
			if "es_ES" in self.language and "es" not in self.language:
				self.language.insert(self.language.index("es_ES")+1,"es")
			self.lang=self.lang.split("_")[0]
			
			if "ca_ES@valencia" in self.language:
				self.language.insert(self.language.index("ca_ES@valencia"),"qcv")
		except:
			fallback_lang()


		if self.language==['']:
			fallback_lang()
			
		groups={}
		
		for item in grp.getgrall():
			if len(item.gr_mem)>0:
				if item.gr_name not in groups:
					groups[item.gr_name]=item.gr_mem
				else:
					groups[item.gr_name]=list(groups[item.gr_name]+item.gr_mem)
			
		
		self.user_groups=[]
		try:
			for item in groups:
				if os.environ["USER"] in groups[item]:
					self.user_groups.append(item)
					
			self.user_groups.append("*")
		except:
			pass
		
	#def create_user_area

	
	def start_gui(self):
		

		self.collapsed_image="/usr/share/icons/breeze-dark/actions/16/arrow-left.svg"
		self.expanded_image="/usr/share/icons/breeze-dark/actions/16/arrow-down.svg"

		self.icon_theme=Gtk.IconTheme()
		self.icon_theme.set_custom_theme("lliurex-neu")
		
		builder=Gtk.Builder()
		if os.path.exists("/srv/svn/pandora/zero-center2/install-files/usr/share/zero-center/rsrc/zero-center.glade"):
			builder.add_from_file("/srv/svn/pandora/zero-center2/install-files/usr/share/zero-center/rsrc/zero-center.glade")
		else:
			builder.add_from_file("/usr/share/zero-center/rsrc/zero-center.glade")
		self.window=builder.get_object("window1")
		self.window.connect("delete_event",self.close_window)
		self.window.set_name("BLACK")
		self.buttons_vbox=builder.get_object("buttons_vbox")
		self.content_hbox=builder.get_object("main_box")
		self.content_hbox.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(0.2,0.2,0.2,1))
		self.window_box=builder.get_object("window_box")
		self.viewport=builder.get_object("viewport1")
		self.viewport.set_name("ORANGE")
		self.category_combobox=builder.get_object("category_combobox")
		self.msg_label=builder.get_object("llx_label")
		self.msg_label.connect("draw",self.drawing_label_event)
		self.msg_label.set_tooltip_text(self.msg_text)
		
		self.hidden_button=builder.get_object("button1")
		self.hidden_button.grab_focus()
		
		self.search_entry=builder.get_object("entry")
		self.search_entry.connect("changed",self.entry_changed)
		
		self.progress_bar=builder.get_object("progressbar")
		self.progress_label=builder.get_object("progress_label")
		self.progress_label.set_name("WHITE")
		
		self.add_categories_to_window("All")
		self.set_css_info()
		
		self.window.connect("key-press-event",self.on_key_press_event)
		
		self.window.show()
		GObject.threads_init()
		Gtk.main()
		
	#def start_gui
	
	
	def on_key_press_event(self,window,event):
		
		ctrl=(event.state & Gdk.ModifierType.CONTROL_MASK)
		if ctrl and event.keyval == Gdk.KEY_f:
			self.search_entry.grab_focus()
		
	#def on_key_press_event	
	
	
	def entry_changed(self,widget):
		self.add_categories_to_window("",False)
	
	def scroll_me(self,img):
		
		if self.msg_x > (self.scroll_width)*-1:
			self.msg_x-=1
		else:
			self.msg_x=401
		img.queue_draw()
		return self.scrolling
		
	#def scroll_me


	def set_msg_label_text(self,txt):
	
		self.msg_text=txt
		self.msg_label.queue_draw()
		
	#def set_msg_label_text()

	
	def drawing_label_event(self,widget,ctx):
		
		lg1 = cairo.LinearGradient(0.0,18.0, 400.0, 18.0)
		lg1.add_color_stop_rgba(0, 0.38, 0.38, 0.38, 1)
		lg1.add_color_stop_rgba(0.1, 0.2, 0.2, 0.2, 1)
		lg1.add_color_stop_rgba(0.9, 0.2, 0.2, 0.2, 1)
		lg1.add_color_stop_rgba(1, 0.38, 0.38, 0.38, 1)
		ctx.rectangle(0, 0, 400, 18)
		ctx.set_source(lg1)
		ctx.fill()

		tmp_text=self.msg_text

		if len(tmp_text)>66:
			if self.drawing_mode:
				if not self.scrolling:
					self.scrolling=True
					self.msg_x=200
					GLib.timeout_add(12,self.scroll_me,widget)
			else:
				tmp_text=tmp_text[:63]
				tmp_text="      " + tmp_text+u" …"
		else:
			self.scrolling=False
			spaces=90-len(tmp_text)
			space="".join([" "]*(spaces/2))
			tmp_text=space+tmp_text+space
			
		
		
		tmp_text=tmp_text.replace("[","<b>[")
		tmp_text=tmp_text.replace("]","] </b>")
		
		x=self.msg_x
		pctx = PangoCairo.create_layout(ctx)
		desc = Pango.font_description_from_string ("Ubuntu 9")
		pctx.set_font_description(desc)
		ctx.set_source_rgb(0.9,0.9,0.9)
		pctx.set_markup(tmp_text)
		self.scroll_width=pctx.get_pixel_size()[0]
		ctx.move_to(x,0)
		PangoCairo.show_layout(ctx, pctx)
		
	#def set_msg_label
	
	
	def set_css_info(self):
		
		css = """
		
		


		/*@define-color arc-blue #3a87e2;*/
		@define-color arc-blue #0062f5;
		@define-color arc-blue-light #4accf5;
		@define-color arc-black #2d323d;
		@define-color arc-red #000000;
		@define-color arc-blue-hover #629de2;
		@define-color arc-blue-active #3aa3e2;
		@define-color default-grey #666666;


		
		#BLACK {
			background-image: -gtk-gradient (linear,	left top, left bottom, from (#1a1a1a),  to (#616161));
			
		}

		#ORANGE {
			background-image: -gtk-gradient (linear,	left top, left bottom, from (#575757),  to (#373737));
			
		}
		
		#BLACKEXPANDER {
			background-image: -gtk-gradient (linear,	left top, left bottom, from (#1a1a1a),  to (#1a1a1a));
			color: white;
			box-shadow: 50px 50px;
			
		}
		
		#WHITE {
			color: white;
			text-shadow: 0px 1px black;
		}		
		
		#WHITE-15 {
			color: white;
			font-size: 15px;
			text-shadow: 1px 2px black;
		}

		
		#BLACKBUTTON{
			background-image: -gtk-gradient (linear,	left top, left bottom, from (#2a2a2a),  to (#616161));
			color: #e0e0e0;
			border-color: #000;
			border-style: none;
			border-radius: 10px;
			
		}
		

		#TRANSPARENTBUTTON{
			padding: 3px 3px;
			border:none;
			border-radius: 50px;
			background-image: none;
			background-color: transparent;
		}
		
		
		#TRANSPARENTBUTTON:hover{
			box-shadow: 0px 0px 5px rgba(255,255,255,0.8);
		}
		
		#APPBUTTON{

			padding: 0px 0px;
			border:none;
			background-image: none;
			box-shadow: none;
			background-color: transparent;
			box-shadow: 0px 2px 5px rgba(0,0,0,0.8);

		}

		#APPBUTTON:hover{

			
			border-width: 0;
			border-radius: 0px;
			border-color: transparent;
			border: none;	
			box-shadow: 0px 1px 8px rgba(0,0,0,1);
		}
		
		GtkSeparator {
			color: rgba(255,255,255,0.8);
		}
		

		.entry 
		{
			color: rgba(255,255,255,0.8);
			border: none;
			/*border-radius: 5px;*/
			background-color: @arc-blue;
			border-bottom: 1px solid #888888;
			padding: 4px;
			background: #2d2d2d;
			
			/*border-bottom: 2px solid transparent;*/
	
		}
		
		.entry:selected
		{
			color: white;
			background: @arc-blue;

		}
		
		.entry:focus
		{
			color: rgba(255,255,255,0.8);
			border-bottom: 1px solid rgba(255,255,255,1);
			/*border-bottom: 2px solid rgba(0,0,0,0);*/
			/*background-color: transparent;*/
		
	
		}

		
		"""
		
		self.style_provider=Gtk.CssProvider()
		self.style_provider.load_from_data(css)
		
		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),self.style_provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		
	#def set_css_info	
	
	
	def get_banner_image(self,app):

		package_rsrc_path=BANNER_PATH
		img_path=package_rsrc_path+"package.png"
		
		for item in os.listdir(package_rsrc_path):
			f,ext=item.split(".")
			if app["Icon"] == f:
				img_path=package_rsrc_path+item
		
		
		img=cairo.ImageSurface.create_from_png(img_path)
		ctx=cairo.Context(img)

		if not self.check_app_dependences(app):
			ctx.set_source_rgba(0.5,0.5,0.5,0.7)
			ctx.rectangle(0,0,235,110)
			ctx.fill()
		

		ctx.set_source_rgba(0,0,0,0.8)
		ctx.rectangle(0,90,235,110)
		ctx.fill()


		show_status=True
		if "Depends" in app:

			if not self.check_app_dependences(app):
				
				lg1 = cairo.LinearGradient(0.0,110.0, 200.0, 110.0)
				lg1.add_color_stop_rgba(0, 0.7, 0, 0, 1)
				lg1.add_color_stop_rgba(1, 1, 0.2, 0.2, 0)
				ctx.rectangle(0, 0, 200, 20)
				ctx.set_source(lg1)
				ctx.fill()
											
				ctx.select_font_face("Ubuntu")
				ctx.set_font_size(15)
				ctx.move_to(5,15)
				ctx.set_source_rgba(1,1,1,app["conf_alpha"])
											
				ctx.show_text(_("Unmet dependences"))
				ctx.stroke()
				
				show_status=False


		if "Service" in app and show_status:

			if app["Service"].lower()=="true":

				if app["configured"]==1:

					lg1 = cairo.LinearGradient(0.0,110.0, 200.0, 110.0)
							       
					lg1.add_color_stop_rgba(0, 0, 0.2, 0, 1)
					lg1.add_color_stop_rgba(1, 0, 1, 0, 0)
					ctx.rectangle(0, 0, 200, 20)
					ctx.set_source(lg1)
					ctx.fill()
							
					ctx.select_font_face("Ubuntu")
					ctx.set_font_size(15)
					ctx.move_to(5,15)
					ctx.set_source_rgb(1,1,1)
							
					ctx.show_text(_("Configured"))
					ctx.stroke()


				elif app["configured"]==0:

					lg1 = cairo.LinearGradient(0.0,110.0, 200.0, 110.0)
							       
					lg1.add_color_stop_rgba(0, 0.7, 0, 0, 1)
					lg1.add_color_stop_rgba(1, 1, 0.2, 0.2, 0)
					ctx.rectangle(0, 0, 200, 20)
					ctx.set_source(lg1)
					ctx.fill()
							
					ctx.select_font_face("Ubuntu")
					ctx.set_font_size(15)
					ctx.move_to(5,15)
					ctx.set_source_rgb(1,1,1)
							
					ctx.show_text(_("Not configured"))
					ctx.stroke()
					
				else:
					lg1 = cairo.LinearGradient(0.0,110.0, 200.0, 110.0)
					lg1.add_color_stop_rgba(0, 1, 0, 0, 1)
					lg1.add_color_stop_rgba(1, 1, 0.2, 0.2, 0)
					ctx.rectangle(0, 0, 200, 20)
					ctx.set_source(lg1)
					ctx.fill()
								
					ctx.select_font_face("Ubuntu")
					ctx.set_font_size(15)
					ctx.move_to(5,15)
					ctx.set_source_rgba(1,1,1,app["conf_alpha"])
								
					ctx.show_text(_("Failed"))
					ctx.stroke()

		ctx.select_font_face("Ubuntu")
		ctx.set_font_size(15)
		ctx.move_to(5,105)
		ctx.set_source_rgb(1,1,1)
		txt=""
		fix=True
		
		text=self.get_name(app)
		
		
		for char in range(30):
			try:
				txt+=text[char]
			except:
				fix=False
				break
							
		if fix:
			txt+="…"
		
		ctx.show_text(txt)
		ctx.stroke()

		#img.write_to_png(self.user_rsrc_path+item)
		image=Gtk.Image()
		#image.set_from_file(self.user_rsrc_path+item)
		image.set_from_pixbuf(Gdk.pixbuf_get_from_surface(img,0,0,235,110))
		image.set_name("BIMAGE")
		return image
		
	#def get_image

	
	def drawing_banner_event(self,widget,ctx,app):
		
		package_rsrc_path=BANNER_PATH
		img_path=package_rsrc_path+"package.png"
		for item in os.listdir(package_rsrc_path):
			f,ext=item.split(".")
			if app["Icon"] == f:
				img_path=package_rsrc_path+item
		
	
		img=cairo.ImageSurface.create_from_png(img_path)
		ctx.set_source_surface(img,0,0)
		
		if not self.check_app_dependences(app):
			ctx.paint_with_alpha(0.2)
			ctx.set_source_rgba(0.5,0.5,0.5,0.7)
			ctx.rectangle(0,0,235,110)
			ctx.fill()
		else:
			ctx.paint()


		if "pulsating" in app and app["pulsating"]:
			
			'''
			if app["pulsating"]:
				ctx.set_source_rgba(1,1,1,app["pulsating_alpha"])
				ctx.rectangle(0,0,235,110)
				ctx.fill()		
			'''
			
			app.setdefault("pulsating_alpha",0.0)
	
			lg1 = cairo.LinearGradient(0.0,10.0, 235.0, 10.0)
			lg1.add_color_stop_rgba(0, 0, 0.0, 0.8, 0.7)
			lg1.add_color_stop_rgba(app["pulsating_alpha"], 0.1, 0.7, 0.9, 1)
			lg1.add_color_stop_rgba(1, 0, 0, 0.8, 0.5)
			ctx.rectangle(0,app["bar_height"],235,20)
			ctx.set_source(lg1)
			ctx.fill()
			ctx.set_source_rgba(0,0,0,0.8)
			ctx.rectangle(0,app["bar_height"]+20,235,110)
			ctx.fill()			
			
		else:
			
			ctx.set_source_rgba(0,0,0,0.7)
			ctx.rectangle(0,app["bar_height"],235,110)
			ctx.fill()
		
		show_status=True
		if "Depends" in app:

			if not self.check_app_dependences(app):
				
				lg1 = cairo.LinearGradient(0.0,110.0, 200.0, 110.0)
				lg1.add_color_stop_rgba(0, 0.7, 0, 0, 1)
				lg1.add_color_stop_rgba(1, 1, 0.2, 0.2, 0)
				ctx.rectangle(0, 0, 200, 20)
				ctx.set_source(lg1)
				ctx.fill()
											
				ctx.select_font_face("Ubuntu")
				ctx.set_font_size(15)
				
				ctx.move_to(6,16)
				ctx.set_source_rgba(0,0,0,app["conf_alpha"])
				ctx.show_text(_("Unmet dependences"))
				ctx.stroke()
				
				
				ctx.move_to(5,15)
				ctx.set_source_rgba(1,1,1,app["conf_alpha"])
				ctx.show_text(_("Unmet dependences"))
				ctx.stroke()
				
				show_status=False

		if "Service" in app and show_status:
			
			if app["Service"].lower()=="true":

				if app["configured"]==1:

					lg1 = cairo.LinearGradient(0.0,110.0, 200.0, 110.0)
					lg1.add_color_stop_rgba(0, 0, 0.2, 0, 1)
					lg1.add_color_stop_rgba(1, 0, 1, 0, 0)
					ctx.rectangle(0, 0, 200, 20)
					ctx.set_source(lg1)
					ctx.fill()
							
					ctx.select_font_face("Ubuntu")
					ctx.set_font_size(15)
					
					ctx.set_source_rgba(0,0,0,app["conf_alpha"])
					ctx.move_to(6,16)		
					ctx.show_text(_("Configured"))
					ctx.stroke()
					
					
					ctx.set_source_rgba(1,1,1,app["conf_alpha"])
					ctx.move_to(5,15)		
					ctx.show_text(_("Configured"))
					ctx.stroke()
							
				elif app["configured"]==-1:

					lg1 = cairo.LinearGradient(0.0,110.0, 200.0, 110.0)
					lg1.add_color_stop_rgba(0, 0.7, 0, 0, 1)
					lg1.add_color_stop_rgba(1, 1, 0.2, 0.2, 0)
					ctx.rectangle(0, 0, 200, 20)
					ctx.set_source(lg1)
					ctx.fill()
							
					ctx.select_font_face("Ubuntu")
					ctx.set_font_size(15)
					
					ctx.set_source_rgba(0,0,0,app["conf_alpha"])
					ctx.move_to(6,16)		
					ctx.show_text(_("Failed"))
					ctx.stroke()
					
					
					ctx.move_to(5,15)
					ctx.set_source_rgba(1,1,1,app["conf_alpha"])
					ctx.show_text(_("Failed"))
					ctx.stroke()
					
				else:
					
					lg1 = cairo.LinearGradient(0.0,110.0, 200.0, 110.0)
					lg1.add_color_stop_rgba(0, 0.8, 0, 0, 1)
					lg1.add_color_stop_rgba(1, 1, 0.2, 0.2, 0)
					ctx.rectangle(0, 0, 200, 20)
					ctx.set_source(lg1)
					ctx.fill()

					ctx.select_font_face("Ubuntu")
					ctx.set_font_size(15)
					
					ctx.set_source_rgba(0,0,0,app["conf_alpha"])
					ctx.move_to(6,16)		
					ctx.show_text(_("Not configured"))
					ctx.stroke()					
					
					ctx.move_to(5,15)
					ctx.set_source_rgba(1,1,1,app["conf_alpha"])
					ctx.show_text(_("Not configured"))
					ctx.stroke()					


		txt=""
		fix=True
		for char in range(30):
			try:
				txt+=self.get_name(app)[char]
			except:
				fix=False
				break
							
		if fix:
			txt+="…"


		ctx.select_font_face("Ubuntu")
		ctx.set_font_size(15)
		
		ctx.move_to(6,app["bar_height"]+16)
		ctx.set_source_rgb(0,0,0)
		ctx.show_text(txt)
		ctx.stroke()		
		
		ctx.move_to(5,app["bar_height"]+15)
		ctx.set_source_rgb(0.9,0.9,0.9)
		ctx.show_text(txt)
		ctx.stroke()		

		
		
		
		y=app["bar_height"]+30
		pctx = PangoCairo.create_layout(ctx)
		desc = Pango.font_description_from_string ("Ubuntu 8")
		pctx.set_font_description(desc)
		pctx.set_alignment(Pango.Alignment.LEFT)
		pctx.set_justify(True)
		pctx.set_width(225000)
		pctx.set_height(10)
		ctx.set_source_rgb(1,1,0.8)
		pctx.set_text(self.get_comment(app),-1)
		

		ctx.move_to(6,y)
		PangoCairo.show_layout (ctx, pctx)
		
		if "custom_text" in app:
			
			ctx.set_source_rgb(0.5,0.5,1)
			pctx.set_text(app["custom_text"],-1)
			ctx.move_to(6,y+60)
			PangoCairo.show_layout (ctx, pctx)
			
		
	#def drawing_event
	

	def mouse_over(self,widget,event,app,img):
		
		if not app["expanding"]:
			app["restoring"]=False
			app["expanding"]=True
			GLib.timeout_add(10,self.expand_black_area,app,img)
		
	#def mouse_over

	
	def mouse_left(self,widget,event,app,img):
		
		if not app["restoring"]:
			app["expanding"]=False
			app["restoring"]=True
			GLib.timeout_add(10,self.restore_black_area,app,img)
		
	#def mouse_left

	
	def expand_black_area(self,app,img):
		
		while app["bar_height"]>0 and app["expanding"]:
			app["bar_height"]-=2
			if app["conf_alpha"]>0.0:
				app["conf_alpha"]-=0.025
			img.queue_draw()
			return True
			
		if not app["expanding"]:
			return False
			
		app["expanding"]=False
		app["conf_alpha"]=0.0
		img.queue_draw()
		return False
		
	#def expand_black_area
	
	
	def restore_black_area(self,app,img):
		
		while app["bar_height"]<BAR_HEIGHT and app["restoring"]:
			app["bar_height"]+=2
			if app["conf_alpha"]<1.0:
				app["conf_alpha"]+=0.025
			img.queue_draw()
			return True
			
		if not app["restoring"]:
			return False
			
		app["restoring"]=False
		app["conf_alpha"]=1.0
		img.queue_draw()
		return False
		
	#def restore_black_area
	
	
	def check_app_groups(self,app,verbose=True):
		
		if verbose:
			sys.stdout.write(" * Checking " + app["ID"] + " ... ")
		groups=[]
		if "Groups" not in app:
			if verbose:
				print("OK")
			return True
		
		try:
			
			if os.environ["USER"]=="root":
				if verbose:
					print("OK")
				return True
			
			groups=app["Groups"].strip("\n").split(";")
			for group in groups:
				if group in self.user_groups:
					if verbose:
						print("OK")		
					return True
			
		except Exception as e:
			print(e)
			pass
			
		if verbose:
			print "NOT ALLOWED"
			print "\t[!] App groups: ",sorted(groups)
		return False
		
	#def check_app_groups

	
	def add_pulsating(self,app,image):
		
		GLib.timeout_add(70,self.pulsate_color,app,image)
		
	#def add_pulsating


	def pulsate_color(self,app,image):
		
		app["pulsating_alpha"]+=app["pulsating_increment"]
		
		if app["pulsating_alpha"] >= 1.0 :
			
			app["pulsating_increment"]=-0.02
			
		if app["pulsating_alpha"] <= 0.0 :
			
			app["pulsating_increment"]=0.02
			
		image.queue_draw()
		return app["pulsating"]
		
	#def pulsate_color
		
		
	def check_app_dependences(self,app):
		
		if "Depends" in app:
			depends=app["Depends"].split(";")
			for dep in depends:
				
				if dep not in self.configured_apps:
					return False
				
		return True
		
	#def check_app_dependences

	
	def add_categories_to_window(self,category,verbose=True):
		
		for child in self.content_hbox.get_children():
			self.content_hbox.remove(child)
		
		for category in self.categories_parser.categories:
			
			icon=category["icon"]
			category=category["name"].lower()
			
			once=True
			hbox=Gtk.FlowBox()
			hbox.set_margin_left(5)
			hbox.set_margin_right(5)
			hbox.set_homogeneous(True)
			hbox.set_column_spacing(5)
			hbox.set_row_spacing(10)
			hbox.set_halign(Gtk.Align.FILL)
			hbox.set_valign(Gtk.Align.START)
			hbox.set_selection_mode(Gtk.SelectionMode.NONE)
			count=0
			if category in self.app_parser.apps:
				for app in sorted(self.app_parser.apps[category]):
					
					if self.check_app_groups(app,verbose):

						search_txt=self.search_entry.get_text().lower().strip()

						if search_txt not in app["ID"] and search_txt not in self.get_translation(app["Category"]).lower() and search_txt not in self.get_name(app).lower() and len(search_txt)>2:
							continue
						button=Gtk.Button()
						button.set_name("APPBUTTON")
						button.set_size_request(235,110)
						#button.set_margin_top(10)
						button.set_halign(Gtk.Align.FILL)
						button.set_valign(Gtk.Align.FILL)
						
						
						if not self.drawing_mode:
							image=self.get_banner_image(app)
						else:
							image=Gtk.DrawingArea()
							
							image.show()
							image.connect("draw",self.drawing_banner_event,app)
							
							if "pulsating" in app:
								if app["pulsating"]:
									app["pulsating_alpha"]=0.0
									app["pulsating_increment"]=0.02
									self.add_pulsating(app,image)
							
							
							button.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
							button.connect("motion-notify-event",self.mouse_over,app,image)
							button.connect("leave_notify_event",self.mouse_left,app,image)
							
							#button.set_size_request(245,120)
						
						button.add(image)
						if "Name["+self.lang+"]" in app:
							button.set_tooltip_text(app["Name["+self.lang+"]"])
						else:
							button.set_tooltip_text(app["Name"])
						button.connect("clicked",self.app_clicked,app)
						app["gtk_button"]=button
						
						child=Gtk.FlowBoxChild()
						child.set_border_width(10)
						child.set_halign(Gtk.Align.START)
						#child.set_size_request(235,110)
						
						child.add(button)
						
						hbox.add(child)
						count+=1
		
			if count!=0:
				hbox.show_all()
				r=Gtk.Revealer()
				if once:
					self.add_label(self.get_translation(category),icon,r)
					once=False
				
				hbox.set_margin_left(20)
				
				r.add(hbox)
				r.set_reveal_child(True)
				r.show_all()
				self.content_hbox.pack_start(r,True,True,5)
		
		if len(self.content_hbox.get_children()) > 0:
			self.content_hbox.get_children()[-1].set_margin_bottom(10)
		
	#def add_categories_to_window
	
	
	
	
	def add_label(self,label_name,icon_name,r):
		
		if icon_name==None:
			icon_name="system"
			
		tmpbox=Gtk.HBox()
		img=Gtk.Image()
		img.set_from_icon_name(icon_name,Gtk.IconSize.MENU)
		label=Gtk.Label(label_name)
		label.set_name("WHITE-15")
		expander=Gtk.HSeparator()
		expander.set_margin_right(15)
		expander.set_valign(Gtk.Align.CENTER)
		tmpbox.set_margin_left(10)
		tmpbox.set_margin_top(5)
		tmpbox.pack_start(img,False,False,0)
		tmpbox.pack_start(label,False,False,10)
		tmpbox.pack_start(expander,True,True,0)
		expand_button=Gtk.Button()
		expand_button.set_valign(Gtk.Align.CENTER)
		if os.path.exists(self.expanded_image):
			expanded_image=Gtk.Image.new_from_file(self.expanded_image)
			expand_button.set_name("TRANSPARENTBUTTON")
		else:
			expanded_image=Gtk.Image.new_from_stock("gtk-go-down",Gtk.IconSize.BUTTON)
		expand_button.set_image(expanded_image)
		expand_button.show_all()
		expand_button.connect("clicked",self.category_label_clicked,r)
		expand_button.set_margin_right(18)
		tmpbox.pack_start(expand_button,False,True,0)
		tmpbox.show_all()
		self.content_hbox.pack_start(tmpbox,False,False,5)		
		
	#def add_label
	
	def category_label_clicked(self,widget,revealer):
		
		state=revealer.get_reveal_child()
		revealer.set_reveal_child(not state)
		if state:
			if os.path.exists(self.collapsed_image):
				image=Gtk.Image.new_from_file(self.collapsed_image)
			else:
				image=Gtk.Image.new_from_stock("gtk-go-back",Gtk.IconSize.BUTTON)
			
			widget.set_image(image)
		else:
			if os.path.exists(self.expanded_image):
				image=Gtk.Image.new_from_file(self.expanded_image)
			else:
				image=Gtk.Image.new_from_stock("gtk-go-down",Gtk.IconSize.BUTTON)
			widget.set_image(image)
			
		
	#def category_label_clicked
	
	def app_clicked(self,widget,app):

		try:
			if  self.client.get_variable("","VariablesManager","MASTER_SERVER_IP"):
				if app["ID"] in self.blacklist:
					result = self.open_dialog("Warning",_("We are in a center model and therefore should install this service on the master \n server to be accessible from any computer in the center, whether to continue \n with the installation on this computer the service is only available on computers \n that are in the internal network of this server."),True)
					if result == Gtk.ResponseType.CANCEL:
						return -1
		except:
			# n4d is not alive. Let's pass this for now 
			pass

		if app["ID"] in self.configured_apps:
			ret=self.open_dialog("Warning",_("<b>%s</b> is already configured. Do you want to execute it again?")%self.get_name(app),True)
			if ret==Gtk.ResponseType.CANCEL:
				return -1
		
		if self.check_app_dependences(app):
		
			cmd=""
				
			if "Using" in app:
				cmd+=app["Using"].strip(" ").strip("\n") +" "
					
			cmd+=self.app_parser.ZMD_PATH + app["ScriptPath"]
			
			gt=False
			if "Gnome-terminal" in app:
				if app["Gnome-terminal"].lower()=="true":
					cmd='gnome-terminal --command="'+cmd+'"'
					gt=True
					
			if not gt:
				if "gnome-terminal" in app:
					if app["gnome-terminal"].lower()=="true":
						cmd='gnome-terminal --command="'+cmd+'"'
				
				
			
			blocked=False
			print(' * Executing "' + cmd + '" ...')
			if "Modal" in app:
				if app["Modal"].lower()=="true" and not self.mprocess.is_alive():
					GLib.timeout_add(250,self.pulse_progress)
					self.progress_bar.show()
					
					try:
						txt="Executing %s"%app["Name["+self.lang+"]"]
					except:
						txt="Executing %s"%app["Name"]
					self.progress_label.set_text(txt)
					self.progress_label.set_max_width_chars(32)
					self.progress_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
					self.progress_label.show()
					self.mprocess_app_name=app["Name"]
					blocked=True
				else:
					self.open_dialog("Warning","<b>%s</b> is being executed. Please wait until it finishes."%self.mprocess_app_name )
					return -1
		
			self.execute(cmd,blocked,app,widget)
			
		else:
			
			self.open_dialog("Warning","<b>%s</b> dependences have not been configured."%self.get_name(app) +"\n[ %s ]"%app["Depends"])
		
	#def app_clicked
	
	
	def check_output(self,process,app,button):
		
		if not process.is_alive():
			
			print "[ZeroCenter] %s has ended"%app["ID"]
			
			if "Service" in app:
				if app["Service"].lower()=="true":
					
					try:
						self.get_states()
			
						for cat in self.app_parser.apps:
							for item in self.app_parser.apps[cat]:
								item["gtk_button"].get_child().queue_draw()
						
						darea=button.get_child()
						darea.queue_draw()
						
					except Exception as e:
						pass
					
		return process.is_alive()
		
	#def check_output
	
	
	def pulse_progress(self):
		
		self.progress_bar.pulse()
		if not self.mprocess.is_alive():
			self.progress_bar.hide()
			self.progress_label.hide()
		return self.mprocess.is_alive()

	#def pulse_progress

	
	def execute(self,cmd,blocked=False,app=None,widget=None):
		
		if not blocked:
			p=multiprocessing.Process(target=self._execute,args=(cmd,))
			#p.daemon=True
			GLib.timeout_add(1000,self.check_output,p,app,widget)
			p.start()
			
		if blocked:
			
			if not self.mprocess.is_alive():
				self.mprocess=multiprocessing.Process(target=self._execute,args=(cmd,))
				#self.mprocess.daemon=True
				self.mprocess.start()
				GLib.timeout_add(1000,self.check_output,self.mprocess,app,widget)
			else:
				self.open_dialog("Warning",_("<b>%s</b> is being executed. Please wait until it finishes.")%self.mprocess_app_name )
		
	#def execute


	def _execute(self,cmd):
		
		
		subprocess.call(cmd,shell=True,preexec_fn=lambda: signal.signal(signal.SIGPIPE,signal.SIG_DFL))
		
		#os.system(cmd)
		
	#def _execute

	
	def close_window(self,widget,data):
		
		if self.mprocess.is_alive():
			ret=self.open_dialog("Warning",_("<b>%s</b> is being executed. Are you sure you want to exit?")%self.mprocess_app_name ,True)
		
			if ret==Gtk.ResponseType.CANCEL:
				return -1
				
			self.mprocess.terminate()
			self.mprocess=multiprocessing.Process()
		
		Gtk.main_quit()
		print("")
		
	#def close_window

		
	def open_dialog(self,title,text,show_cancel=False):

		label = Gtk.Label()
		label.set_markup(text)
		if show_cancel:
			dialog = Gtk.Dialog(title, None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL))
		else:
			dialog = Gtk.Dialog(title, None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
		hbox = Gtk.HBox()
		img=Gtk.Image.new_from_icon_name("emblem-important",Gtk.IconSize.DIALOG)
		hbox.pack_start(img,True,True,5)
		hbox.pack_start(label,True,True,10)
		hbox.show_all()
		dialog.vbox.pack_start(hbox,True,True,10)
		dialog.set_border_width(6)
		response = dialog.run()
		dialog.destroy()
		return response
		
	#def open_dialog

	
	def get_state(self,app):

		try:
			configured=self.client.get_state("","ZCenterVariables",app["ID"])
			return configured
		except:
			return 0
		
	#def get_state

	
	def set_configured(self,app,key):
		
		if app in self.app_parser.app_list:
			
			try:
				self.client.set_configured(key,"ZCenterVariables",app)
			except Exception as e:
				print(e)
				
		else:
			print("[!] %s is not installed"%app)
		
		sys.exit(0)
				
	#def set_configured

	
	def set_non_configured(self,app,key):
		
		if app in self.app_parser.app_list:
			
			try:
				self.client.set_non_configured(key,"ZCenterVariables",app)
			except:
				pass
				
		else:
			print("\t[!] %s is not installed"%app)
		
		sys.exit(0)
		
	#def set_non_configured
	
	def set_failed(self,app,key):
		
		if app in self.app_parser.app_list:
			
			try:
				self.client.set_failed(key,"ZCenterVariables",app)
			except:
				pass
				
		else:
			print("\t[!] %s is not installed"%app)
		
		sys.exit(0)
		
	#def set_non_configured

	
	def set_custom_text(self,app,text,key):
		
		if app in self.app_parser.app_list:
			
			try:
				self.client.set_custom_text(key,"ZCenterVariables",app,text)
			except:
				pass
				
		else:
			print("\t[!] %s is not installed"%app)
		
		sys.exit(0)
		
	#def set_custom_text

	
	def add_pulsating_color(self,key,app):
		
		try:
			self.client.add_pulsating_color(key,"ZCenterVariables",app)
		except:
			pass
			
		sys.exit(0)
		
	#def add_pulsating_color

	
	def remove_pulsating_color(self,key,app):
		
		try:
			self.client.remove_pulsating_color(key,"ZCenterVariables",app)
		except:
			pass
		
		sys.exit(0)
		
	#def add_pulsating_color

	
	def add_zc_notification(self,key,app,text,text_es="",text_qcv=""):
		
		try:
			self.client.set_zc_message(key,"ZCenterVariables",app,text,text_es,text_qcv)
		except Exception as e:
			print(e)
			
		sys.exit(0)
		
	#def add_zc_notification

	
	def remove_zc_notification(self,key,app):
		
		try:
			self.client.remove_zc_message(key,"ZCenterVariables",app)
		except Exception as e:
			print(e)
			
		sys.exit(0)
		
	#def remove_zc_notification


	def usage(self):
		
		print("USAGE:")
		print("\tzero-center [ OPTION [ APP ] ]")
		print("Options:")
		print("\tset-configured APP") 
		print("\tset-non-configured APP") 
		print("\tset-custom-text APP TEXT") 
		print("\tadd-zero-center-notification APP TEXT_EN [TEXT_ES TEXT_QCV]") 
		print("\tremove-zero-center-notification APP") 
		print("\tadd-pulsating-color APP") 
		print("\tremove-pulsating-color APP") 
		print("\tnon-animated")
		print("\tanimated")
		print("\thelp")
		print("")
		sys.exit(0)
		
	#def usage
	

def check_root():
	try:
		f=open("/etc/n4d/key","r")
		key=f.readline().strip("\n")
		f.close()
		return key
	except:
		print("[!] You need root privileges to execute this option [!]")
		sys.exit(1)

if __name__=="__main__":
	
	zc=ZeroCenter()
	zc.drawing_mode=True

	if len(sys.argv)>=2:
		
		if sys.argv[1] not in zc.commands:
			zc.usage()
			sys.exit(1)
			
		if sys.argv[1] == "help":
			zc.usage()
			
		if sys.argv[1] == "set-configured":
			key=check_root()
			zc.set_configured(sys.argv[2],key)
			
		if sys.argv[1] == "set-non-configured":
			key=check_root()
			zc.set_non_configured(sys.argv[2],key)
			
		if sys.argv[1] == "set-failed":
			key=check_root()
			zc.set_failed(sys.argv[2],key)
			
		if sys.argv[1] == "set-custom-text":
			key=check_root()
			zc.set_custom_text(sys.argv[2],sys.argv[3],key)
			
		if sys.argv[1] == "add-zero-center-notification":
			key=check_root()
			
			try:
				app=sys.argv[2]
			except:
				zc.usage()
			try:
				text=sys.argv[3]
			except:
				zc.usage()
			try:
				text_es=sys.argv[4]
			except Exception as e:
				print(e)
				text_es=""
			try:
				text_qcv=sys.argv[5]
			except Exception as e:
				print(e)
				text_qcv=""
			
			zc.add_zc_notification(key,app,text,text_es,text_qcv)
			
		if sys.argv[1] == "remove-zero-center-notification":
			
			key=check_root()
			
			try:
				app=sys.argv[2]
			except:
				zc.usage()
				
			zc.remove_zc_notification(key,app)
			
		if sys.argv[1] == "add-pulsating-color":
			key=check_root()
			try:
				app=sys.argv[2]
			except:
				zc.usage()
				
			zc.add_pulsating_color(key,app)
				
		if sys.argv[1] == "remove-pulsating-color":
			key=check_root()
			
			try:
				app=sys.argv[2]
			except:
				zc.usage()
				
			zc.remove_pulsating_color(key,app)
			

		if sys.argv[1]=="animated":
			zc.drawing_mode=True
			
		if sys.argv[1]=="non-animated":
			zc.drawing_mode=False
		
	
	
	zc.start_gui()

