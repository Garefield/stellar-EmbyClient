import requests
import json
import urllib3
import zipfile
import gzip

class emby_client:
    def __init__(self):
        self.mainurl = "http://111.emby999.com:8096/"
        self.token = ""
        self.userid = ""
        self.username = "RLZ025"
        self.password = "654321"
        self.viewdata = []
        self.viewmenu =  None
        self.itemdata = []
    
    def Login(self,host,user,pwd):
        self.mainurl = host + "/"
        self.username = user
        self.password = pwd
        loginurl = self.mainurl  + "Users/AuthenticateByName?Username=" + self.username + "&pw=" + self.password 
        res =  requests.post(loginurl, headers={'x-emby-authorization': 'MediaBrowser Client="py_client", Device="PY-CLI", DeviceId="None", Version="1.0"'})
        reqcode = res.status_code
        if reqcode != 200:
            res.close()
            del(res)
            print(loginurl)
            return
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        if "User" not in jsondata or "AccessToken" not in jsondata:
            print(jsondata)
            return
        self.userid = jsondata["User"]["Id"]
        self.token = jsondata["AccessToken"]
        print(self.userid)
        print(self.token)
    
    def LoadView(self):
        self.viewdata = []
        loadviewurl = self.mainurl + "Users/" + self.userid + "/Views?api_key=" + self.token
        res =  requests.get(loadviewurl)
        reqcode = res.status_code
        if reqcode != 200:
            res.close()
            del(res)
            print(loadviewurl)
            return
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        if "TotalRecordCount" not in jsondata:
            print(jsondata)
            return
        for item in jsondata["Items"]:
            imgurl = self.GetImgUrl(item,450,300,1)
            newdata = {"name":item["Name"],"id":item["Id"],"type":item["Type"],"CollectionType":item["CollectionType"],"picture":imgurl}
            self.viewdata.append(newdata)
        return
        
    def GetViewMenu(self,viewid):
        viewmenu = None
        for item in self.viewdata:
            if viewid == item["id"]:
                if item["CollectionType"] == "movies":
                    viewmenu = {"name":item["name"],"viewtype":item["CollectionType"],"parentid":viewid,"menu":[{"name":"电影"},{"name":"最近"},{"name":"预告片"},{"name":"播放列表"},{"name":"类型风格"},{"name":"喜欢"},{"name":"文件夹"}]}
                if item["CollectionType"] == "tvshows":
                    viewmenu = {"name":item["name"],"viewtype":item["CollectionType"],"parentid":viewid,"menu":[{"name":"节目"},{"name":"最近"},{"name":"即将播出"},{"name":"喜欢"},{"name":"类型风格"},{"name":"发行公司"},{"name":"单集"},{"name":"文件夹"}]} 
                if item["CollectionType"] == "music":
                    viewmenu = {"name":item["name"],"viewtype":item["CollectionType"],"parentid":viewid,"menu":[{"name":"最近"},{"name":"专辑"},{"name":"专辑艺术家"},{"name":"艺术家"},{"name":"作曲家"},{"name":"类型风格"},{"name":"单曲"},{"name":"文件夹"}]} 
                if item["CollectionType"] == "homevideos":
                    viewmenu = {"name":item["name"],"viewtype":item["CollectionType"],"parentid":viewid,"menu":[{"name":"视频"},{"name":"照片"},{"name":"文件夹"}]} 
                if item["CollectionType"] == "audiobooks":
                    viewmenu = {"name":item["name"],"viewtype":item["CollectionType"],"parentid":viewid,"menu":[{"name":"最近"},{"name":"文件夹"}]} 
                break
        return viewmenu
        
    def GetMovies(self,parentid,menu):
        url = self.mainurl
        parmers = "?SortOrder=Ascending&api_key=" + self.token + "&parentId=" + str(parentid)
        if menu == "电影":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&IncludeItemTypes=Movie&SortBy=SortName&Recursive=true"
        elif menu == "最近":
            url = url + "Users/" + self.userid + "/Items" +  "/Latest" + parmers + "&SortBy=SortName&Recursive=true"
        elif menu == "预告片":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&IncludeItemTypes=Trailer&SortBy=SortName&Recursive=true"
        elif menu == "播放列表":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&IncludeItemTypes=Playlist&SortBy=SortName&Recursive=true"
        elif menu == "类型风格":
            url = url + "/Genres" + parmers + "&SortBy=SortName&Recursive=true"
        elif menu == "喜欢":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&IncludeItemTypes=Movie&Filters=IsFavorite&SortBy=SortName&Recursive=true"
        elif menu == "文件夹":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&IncludeItemTypes=Movie&SortBy=IsFolder%2CFilename&Recursive=false"
        else:
            return []
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return []
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        print(url)
        if "Items" not in jsondata:
            return jsondata
        else:
            return jsondata["Items"]
            
    def GetTVs(self,parentid,menu):
        url = self.mainurl
        parmers = "?api_key=" + self.token + "&parentId=" + str(parentid)
        if menu == "节目":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&IncludeItemTypes=Series&SortBy=SortName&Recursive=true"
        elif menu == "最近":
            url = url + "Users/" + self.userid + "/Items" +  "/Latest" + parmers + "&IncludeItemTypes=Episode&SortBy=SortName&Recursive=true"
        elif menu == "即将播出":
            url = url + "/Shows/Upcoming" + parmers + "&SortOrder=Ascending&SortBy=SortName"
        elif menu == "喜欢Serie" or menu == "喜欢":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&SortOrder=Ascending&SortBy=SortName&IncludeItemTypes=Series&Recursive=true&IsFavorite=true"
        elif menu == "喜欢Episode":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&SortOrder=Ascending&SortBy=SeriesName%2CSortName&IncludeItemTypes=Episode&Recursive=true&IsFavorite=true"
        elif menu == "类型风格":
            url = url + "/Genres" + parmers + "&SortOrder=Ascending&SortBy=SortName&IncludeItemTypes=Series&Recursive=true"
        elif menu == "发行公司":
            url = url + "/Studios" + parmers + "&SortOrder=Ascending&SortBy=SortName&IncludeItemTypes=Series&Recursive=true"
        elif menu == "单集":
             url = url + "Users/" + self.userid + "/Items" + parmers + "&SortOrder=Ascending&SortBy=SeriesSortName%2CParentIndexNumber%2CIndexNumber%2CSortName&IncludeItemTypes=Episode&Recursive=true"
        elif menu == "文件夹":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&SortOrder=Ascending&SortBy=IsFolder%2CFilename&Recursive=false"
        else:
            return []
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return []
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        print(url)
        if "Items" not in jsondata:
            return jsondata
        else:
            return jsondata["Items"]
            
    def GetMusics(self,parentid,menu):
        url = self.mainurl
        parmers = "?api_key=" + self.token + "&parentId=" + str(parentid)
        if menu == "最新":
            url = url + "Users/" + self.userid + "/Items/Latest" + parmers + "&Limit=24"
        elif menu == "最近":
            url = url + "Users/" + self.userid + "/Items/Latest" + parmers + "&SortOrder=Descending&SortBy=DatePlayed&Limit=24"
        elif menu == "多次播放":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&SortBy=DatePlayed&SortOrder=Descending&IncludeItemTypes=Audio&Recursive=true&Filters=IsPlayed&Limit=12"
        elif menu == "专辑":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&Recursive=true&IncludeItemTypes=MusicAlbum"
        elif menu == "专辑艺术家":
            url = url + "Artists/AlbumArtists" + parmers +"&SortBy=SortName&SortOrder=Ascending&Recursive=true&ArtistType=AlbumArtist&userId=" + self.userid
        elif menu == "艺术家":
            url = url + "Artists" + parmers + "&SortBy=SortName&SortOrder=Ascending&Recursive=true&ArtistType=Artist%2CAlbumArtist&userId=" + self.userid
        elif menu == "作曲家":
            url = url + "Artists" + parmers + "&SortBy=SortName&SortOrder=Ascending&Recursive=true&ArtistType=Composer&userId=" + self.userid
        elif menu == "类型风格":
            url = url + "MusicGenres" + parmers + "&userId=" + self.userid
        elif menu == "单曲":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&SortBy=SortName&SortOrder=Ascending&IncludeItemTypes=Audio&Recursive=true"
        elif menu == "文件夹":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&SortOrder=Ascending&SortBy=IsFolder%2CFilename&Recursive=false"
        else:
            return []
        print(url)
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return []
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        print(url)
        if "Items" not in jsondata:
            return jsondata
        else:
            return jsondata["Items"]    
    
    def GetBookAudios(self,parentid,menu):
        url = self.mainurl
        parmers = "?api_key=" + self.token + "&parentId=" + str(parentid)
        if menu == "最近":
            url = url + "Users/" + self.userid + "/Items/Latest" + parmers + "&Limit=24"
        elif menu == "文件夹":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&SortOrder=Ascending&SortBy=IsFolder%2CFilename&Recursive=false"
        else:
            return []
        print(url)
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return []
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        print(url)
        if "Items" not in jsondata:
            return jsondata
        else:
            return jsondata["Items"]    

        
        
    def GetHomeVideo(self,parentid,menu):
        url = self.mainurl
        parmers = "?api_key=" + self.token + "&parentId=" + str(parentid)
        if menu == "视频":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&IncludeItemTypes=Movie&SortBy=SortName&Recursive=true"
        if menu == "照片":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&IncludeItemTypes=Image&SortBy=SortName&Recursive=true"
        if menu == "文件夹":
            url = url + "Users/" + self.userid + "/Items" + parmers + "&SortOrder=Ascending&SortBy=IsFolder%2CFilename&Recursive=false"
        print(url)
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return None
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        print(url)
        if "Items" not in jsondata:
            return jsondata
        else:
            return jsondata["Items"]    
            
    def GetItem(self,itemid):
        url = self.mainurl + "Users/" + self.userid + "/Items/" + str(itemid) + "?api_key=" + self.token
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return None
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        return jsondata
        
    def GetChilds(self,parentid,sort):
        url = self.mainurl + "Users/" + self.userid + "/Items?ParentId=" + str(parentid) + "&SortBy=" + sort + "&SortOrder=Ascending&api_key=" + self.token
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return None
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        return jsondata["Items"]
            
    def GetGenreItems(self,parentid,genreid):
        url = self.mainurl + "Users/" + self.userid + "/Items?ParentId=" + str(parentid) + "&GenreIds=" + str(genreid) + "&SortBy=SortName&SortOrder=Ascending&api_key=" + self.token
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return None
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        return jsondata["Items"]
            
    def GetSeasons(self,seriesid):
        url = self.mainurl + "Shows/" + str(seriesid) + "/Seasons?UserId=" + self.userid + "&api_key=" + self.token
        print(url)
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return None
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        return jsondata["Items"]
        
    def GetEpisodes(self,seriesid,seasonid):
        url = self.mainurl + "Shows/" + str(seriesid) + "/Episodes?SeasonId=" + str(seasonid) + "&api_key=" + self.token
        print(url)
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return None
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        return jsondata["Items"]
        
    def GetStudioItems(self,parentid,studioid):
        url = self.mainurl + "Users/" + self.userid + "/Items?ParentId=" + str(parentid) + "&SortBy=SortName&SortOrder=Ascending&Recursive=true&StudioIds=" + str(studioid) + "&api_key=" + self.token
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return None
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        return jsondata["Items"]
    
    def GetMusicArtistAudio(self,artistid):
        url = self.mainurl + "Users/" + self.userid + "/Items?ArtistIds=" + str(artistid) + "&Recursive=true&IncludeItemTypes=Audio%2CMusicAlbum&SortOrder=Ascending&SortBy=Album%2CPlayCount%2CSortName&api_key=" + self.token
        print(url)
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return None
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        return jsondata["Items"]
       
    def GetMusicArtistAlbum(self,artistid):
        url = self.mainurl + "Users/" + self.userid + "/Items?AlbumArtistIds=" + str(artistid) + "&Recursive=true&SortOrder=Descending%2CAscending&IncludeItemTypes=MusicAlbum&SortBy=ProductionYear%2CSortName&api_key=" + self.token
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return None
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        return jsondata["Items"]
        
    def GetMusicGenre(self,parentid,genreid):
        url = self.mainurl + "Users/" + self.userid + "/Items?SortBy=SortName&SortOrder=Ascending&IncludeItemTypes=MusicAlbum%2CMusicVideo&ParentId=" + str(parentid) +"&GenreIds=" + str(genreid) + "&Recursive=true&api_key=" + self.token
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return None
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        return jsondata["Items"]
        
    def GetFolder(self,folderid):  
        url = self.mainurl + "Users/" + self.userid + "/Items?SortBy=IsFolder%2CFilename&SortOrder=Ascending&ParentId=" + str(folderid) + "&api_key=" + self.token
        res =  requests.get(url)
        reqcode = res.status_code
        if reqcode != 200:
            print(url)
            return None
        jsondata = json.loads(res.text, strict = False)
        res.close()
        del(res)
        return jsondata["Items"]
        
    def IsVirtual(self,item):
        if "LocationType" not in item:
            return False
        if item["LocationType"] == "Virtual":
            return True
        else:
            return False
            
    def GetImgUrl(self,item,maxwidth,maxheight,imgtypeindex):
        imgtype = ""
        tag = ""
        strid = str(item["Id"]) 
        if imgtypeindex == 1:
            if "Primary" in item["ImageTags"]:
                tag = item["ImageTags"]["Primary"]
                imgtype = "Primary"
            elif "Thumb" in item["ImageTags"]:
                tag = item["ImageTags"]["Thumb"]
                imgtype = "Thumb"
            elif item["Type"] == "Audio":
                if "AlbumPrimaryImageTag" in item:
                    imgtype = "Primary"
                    tag = item["AlbumPrimaryImageTag"]
                    strid = str(item["AlbumId"])
            elif item["Type"] == "Season":
                if "SeriesPrimaryImageTag" in item:
                    imgtype = "Primary"
                    tag = item["SeriesPrimaryImageTag"]
                    strid = str(item["SeriesId"])
            elif item["Type"] == "Episode":
                if "SeriesPrimaryImageTag" in item:
                    imgtype = "Primary"
                    tag = item["SeriesPrimaryImageTag"]
                    strid = str(item["SeriesId"])
                elif "ParentBackdropImageTags" in item:
                    if len(item["ParentBackdropImageTags"]) > 0:
                        imgtype = "Backdrop"
                        tag = item["ParentBackdropImageTags"][0]
                        strid = str(item["ParentBackdropItemId"])
            #else:
            #    return self.mainurl + "Items/" + strid + "/Images/Primary?maxWidth=" + str(maxwidth) + "&quality=90"
        if imgtype == "" or imgtypeindex == 2 :
            imgtype = "Backdrop"
            if len(item["BackdropImageTags"]) == 0:
                return self.mainurl + "Items/" + strid + "/Images/Backdrop?maxWidth=" + str(maxwidth) + "&quality=90"
            tag = item["BackdropImageTags"][0]
        if imgtype == "":
            return ""
        res = self.mainurl + "Items/" + strid + "/Images/" + imgtype + "?maxHeight=" + str(maxheight) + "&maxWidth=" + str(maxwidth) + "&tag=" + tag + "&quality=90"
        return res
        
'''           
if __name__ == '__main__':
    embyClient = emby_client()
    embyClient.Login("RLZ025","654321")
    embyClient.LoadView()
    embyClient.itemdata =  embyClient.GetMusics(150103,"文件夹")
    if embyClient.itemdata is not None:
        print(embyClient.itemdata)
        print(len(embyClient.itemdata))
'''