import time
import StellarPlayer
import math
from . import json5
import json
import os
import sys
import bs4
import urllib3
import requests
import threading
import time
from shutil import copyfile
import base64
from .emby_test import emby_client


class embyplugin(StellarPlayer.IStellarPlayerPlugin):
    def __init__(self,player:StellarPlayer.IStellarPlayer):
        super().__init__(player)
        self.embyClient = emby_client()
        self.host = ""
        self.username = ""
        self.password = ""
        self.mainview = []
        self.moviedatas = {}
        self.pagedatas = {}
        self.pagemenus = {}
    
    def start(self):
        super().start()
        
   
    def show(self):
        if hasattr(self.player, 'createTab'):
            self.showMainView()
        else:
            self.player.showText('播放器版本过低，不支持此插件,请升级播放器')
    
    def showMainView(self):
        controls = self.makeMainView()
        self.player.createTab('首页','首页', controls)
        


    def makeMainView(self):
        mainview_layout = [
            [
                {
                    'group': [
                        {'type':'image','name':'picture', '@click':'on_mainview_click'},
                        {'type':'link','name':'name','textColor':'#ff7f00','fontSize':15,'height':0.15, '@click':'on_mainview_click'}
                    ],
                    'dir':'vertical'
                }
            ]
        ]
    
        controls = [
            {'group':
                [
                    {'type':'space','height':5},
                    {'type':'edit','name':'ip_edit','value':self.host,'label':'emby服务端地址','width':300,'height':25},
                    {'type':'space','height':5},
                    {'type':'edit','name':'user_edit','value':self.username,'label':'用 户 名','width':300,'height':25},
                    {'type':'space','height':5},
                    {'group':
                        [
                            {'type':'edit','name':'pwd_edit','value':self.password, 'label':'密      码','width':300},
                            {'type':'space','width':50},
                            {'type':'button','name':'连接','width':60,'@click':'onConnect'}
                        ],
                        'height':25
                    }
                ],
                'dir':'vertical',
                'height':120
            },
            {
                'group': [
                    {'type':'grid','name':'viewgrid','itemlayout':mainview_layout,'value':self.mainview,'itemheight':300,'itemwidth':150,'width':1.0}
                ]
            }
        ]
        return controls
    
    def onConnect(self,*args):
        self.host = self.player.getControlValue('首页','ip_edit').strip()
        self.username = self.player.getControlValue('首页','user_edit').strip()
        self.password = self.player.getControlValue('首页','pwd_edit').strip()
        self.embyClient.Login(self.host,self.username,self.password)
        self.embyClient.LoadView()
        self.mainview.clear()
        for it in self.embyClient.viewdata:
            newit = {"name":it["name"],"id":it["id"],"type":it["type"],"CollectionType":it["CollectionType"],"picture":it["picture"],"data":[]}
            self.mainview.append(newit)
        self.player.updateControlValue('首页','viewgrid',self.mainview)
        
    def on_mainview_click(self,page, listControl, item, itemControl):
        parentid = self.mainview[item]["id"]
        viewMenu = self.embyClient.GetViewMenu(parentid)
        items = []
        if viewMenu["viewtype"] == "movies":
            items = self.embyClient.GetMovies(parentid,"最近")
        if viewMenu["viewtype"] == "tvshows":
            items = self.embyClient.GetTVs(parentid,"最近")
        if viewMenu["viewtype"] == "music":
            items = self.embyClient.GetMusics(parentid,"最近")
        if viewMenu["viewtype"] == "audiobooks":
            items = self.embyClient.GetBookAudios(parentid,"最近")
        itdata = []
        for it in items:
            imgurl = self.embyClient.GetImgUrl(it,450,300,1)
            itdata.append({"name":it["Name"],"id":it["Id"],"type":it["Type"],"picture":imgurl})
        self.mainview[item]["data"] = itdata
        controls = self.makeMainMenu(viewMenu["menu"],itdata)
        self.player.createTab(self.mainview[item]["name"],self.mainview[item]["name"], controls)
        self.pagemenus[self.mainview[item]["name"]] = viewMenu
        self.pagedatas[self.mainview[item]["name"]] = itdata
        
    def makeMainMenu(self,menu,data):
        menudetail_layout = [
            [
                {
                    'group': [
                        {'type':'image','name':'picture', '@click':'on_item_click'},
                        {'type':'link','name':'name','textColor':'#ff7f00','fontSize':12,'height':0.2, '@click':'on_item_click'}
                    ],
                    'dir':'vertical'
                }
            ]
        ]
        menu_layout =[
            [
                {
                    'group': [
                        {'type':'link','name':'name','textColor':'#ff7f00','fontSize':15,'height':1.0, '@click':'on_menu_click'}
                    ],
                    'dir':'vertical'
                }
            ]
        ]
        controls = [
            {'group':
                [
                    {'type':'grid','name':'menugrid','itemlayout':menu_layout,'value':menu,'itemheight':40,'itemwidth':100,'width':1.0}
                ],
                'dir':'vertical',
                'height':60
            },
            {
                'group': [
                    {'type':'grid','name':'viewgrid','itemlayout':menudetail_layout,'value':data,'itemheight':300,'itemwidth':150,'width':1.0}
                ]
            }
        ]
        return controls
    
    def getmenuid(self,page):
        i = 0
        for i in range(len(self.mainview) + 1):
            if self.mainview[i]["name"] == page:
                return i
        return -1
            
    def on_menu_click(self,page, listControl, item, itemControl):
        viewMenu = self.pagemenus[page]
        parentid = viewMenu["parentid"]
        menutitle = viewMenu["menu"][item]["name"]
        print(menutitle)
        items = []
        if viewMenu["viewtype"] == "movies":
            items = self.embyClient.GetMovies(parentid,menutitle)
        if viewMenu["viewtype"] == "tvshows":
            items = self.embyClient.GetTVs(parentid,menutitle)
        if viewMenu["viewtype"] == "music":
            items = self.embyClient.GetMusics(parentid,menutitle)
        if viewMenu["viewtype"] == "audiobooks":
            items = self.embyClient.GetBookAudios(parentid,menutitle)
        itdata = []
        for it in items:
            imgurl = self.embyClient.GetImgUrl(it,450,300,1)
            if imgurl == "":
                imgurl = self.embyClient.GetImgUrl(it,300,450,2)
            name = it["Name"]
            if it["Type"] == "Episode":
                if "IndexNumber" in it:
                    name = it["SeriesName"] + " " +  it["SeasonName"] + "  第" + str(it["IndexNumber"]) + "集"
                else:
                    name =  it["SeriesName"] + " " + it["SeasonName"] + " " +  it["Name"]
            itdata.append({"name":name,"id":it["Id"],"type":it["Type"],"picture":imgurl})
        self.pagedatas[page] = itdata
        self.player.updateControlValue(page,'viewgrid',itdata)
        
       
        
    def onMovie(self,data):
        if len(data["MediaSources"]) > 0:
            if "LocationType" in data:
                if data["LocationType"] == "Virtual":
                    return
            url = data["MediaSources"][0]["Path"]
            self.player.play(url)
            
    def onPlaylist(self,playlistid,page):
        items = self.embyClient.GetChilds(playlistid,"ListItemOrder")
        itdata = []
        for it in items:
            imgurl = self.embyClient.GetImgUrl(it,450,300,1)
            itdata.append({"name":it["Name"],"id":it["Id"],"type":it["Type"],"picture":imgurl})
        self.pagedatas[page] = itdata
        self.player.updateControlValue(page,'viewgrid',itdata)
        
    def onGenre(self,genreid,page):
        parentid = self.pagemenus[page]["parentid"]
        items = self.embyClient.GetGenreItems(parentid,genreid)
        itdata = []
        for it in items:
            imgurl = self.embyClient.GetImgUrl(it,450,300,1)
            itdata.append({"name":it["Name"],"id":it["Id"],"type":it["Type"],"picture":imgurl})
        self.pagedatas[page] = itdata
        self.player.updateControlValue(page,'viewgrid',itdata)
        
    def onSeries(self,seriesid,page):
        items = self.embyClient.GetSeasons(seriesid)
        itdata = []
        for it in items:
            imgurl = self.embyClient.GetImgUrl(it,450,300,1)
            itdata.append({"name":it["Name"],"id":it["Id"],"type":it["Type"],"picture":imgurl})
        self.pagedatas[page] = itdata
        self.player.updateControlValue(page,'viewgrid',itdata)
        
    def onSeason(self,seasonid,page):
        itemdetail = self.embyClient.GetItem(seasonid)
        if itemdetail is  None:
            return
        seriesid = itemdetail["SeriesId"]
        items = self.embyClient.GetEpisodes(seriesid,seasonid)
        itdata = []
        for it in items:
            imgurl = self.embyClient.GetImgUrl(it,300,450,1)
            name = it["SeasonName"]
            if "IndexNumber" in it:
                name = name + " 第" + str(it["IndexNumber"]) + "集"
            else:
                name = name + " " + it["Name"]
            itdata.append({"name":name,"id":it["Id"],"type":it["Type"],"picture":imgurl})
        self.pagedatas[page] = itdata
        self.player.updateControlValue(page,'viewgrid',itdata)
        
    def onStudio(self,studioid,page):
        parentid = self.pagemenus[page]["parentid"]
        items = self.embyClient.GetStudioItems(parentid,studioid)
        itdata = []
        for it in items:
            imgurl = self.embyClient.GetImgUrl(it,450,300,1)
            itdata.append({"name":it["Name"],"id":it["Id"],"type":it["Type"],"picture":imgurl})
        self.pagedatas[page] = itdata
        self.player.updateControlValue(page,'viewgrid',itdata)
        
    def onMusicAlbum(self,musicalbumid,page):
        items = self.embyClient.GetChilds(musicalbumid,"SortName")
        itdata = []
        for it in items:
            imgurl = self.embyClient.GetImgUrl(it,450,300,1)
            itdata.append({"name":it["Name"],"id":it["Id"],"type":it["Type"],"picture":imgurl})
        self.pagedatas[page] = itdata
        self.player.updateControlValue(page,'viewgrid',itdata)
        
    def onMusicArtist(self,artistid,page):    
        items = self.embyClient.GetMusicArtistAudio(artistid)
        itdata = []
        if items is not None:
            for it in items:
                imgurl = self.embyClient.GetImgUrl(it,450,300,1)
                name = it["Name"]
                if it["Type"] == "Audio":
                    name = "歌曲:" + name
                if it["Type"] == "MusicAlbum":
                    name = "专辑:" + name
                itdata.append({"name":name,"id":it["Id"],"type":it["Type"],"picture":imgurl})
        self.pagedatas[page] = itdata
        self.player.updateControlValue(page,'viewgrid',itdata)
        
    def onMusicGenre(self,genreid,page):
        parentid = self.pagemenus[page]["parentid"]
        items = self.embyClient.GetMusicGenre(parentid,genreid)
        itdata = []
        for it in items:
            imgurl = self.embyClient.GetImgUrl(it,450,300,1)
            itdata.append({"name":it["Name"],"id":it["Id"],"type":it["Type"],"picture":imgurl})
        self.pagedatas[page] = itdata
        self.player.updateControlValue(page,'viewgrid',itdata)
        
    def onFolder(self,genreid,page):
        items = self.embyClient.GetFolder(genreid)
        itdata = []
        for it in items:
            imgurl = self.embyClient.GetImgUrl(it,450,300,1)
            itdata.append({"name":it["Name"],"id":it["Id"],"type":it["Type"],"picture":imgurl})
        self.pagedatas[page] = itdata
        self.player.updateControlValue(page,'viewgrid',itdata)
       
    def on_item_click(self,page, listControl, item, itemControl):
        itemid = self.pagedatas[page][item]["id"]
        itemtype = self.pagedatas[page][item]["type"]
        print(itemtype)
        if itemtype == "Movie" or itemtype == "Episode" or itemtype == "Audio" :
            print(itemid)
            itemdata = self.embyClient.GetItem(itemid)
            if itemdata is None:
                return
            self.onMovie(itemdata)
        elif itemtype == "Playlist":
            self.onPlaylist(itemid,page)
        elif itemtype == "Genre":
            self.onGenre(itemid,page)
        elif itemtype == "Series":
            self.onSeries(itemid,page)
        elif itemtype == "Season":
            self.onSeason(itemid,page)
        elif itemtype == "Studio":
            self.onStudio(itemid,page)
        elif itemtype == "MusicAlbum":
            self.onMusicAlbum(itemid,page)
        elif itemtype == "MusicArtist":
            self.onMusicArtist(itemid,page)
        elif itemtype == "MusicGenre":
            self.onMusicGenre(itemid,page)
        elif itemtype == "Folder":
            self.onFolder(itemid,page)
            
                
def newPlugin(player:StellarPlayer.IStellarPlayer,*arg):
    plugin = embyplugin(player)
    return plugin

def destroyPlugin(plugin:StellarPlayer.IStellarPlayerPlugin):
    plugin.stop()