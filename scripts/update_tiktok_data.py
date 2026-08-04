"""Build data.js from the public THE BOYZ TikTok folders on Google Drive."""
import concurrent.futures,json,os,re,time,urllib.parse,urllib.request
from pathlib import Path

API_KEY=os.environ.get("GOOGLE_DRIVE_API_KEY","").strip()
FOLDER_MIME="application/vnd.google-apps.folder"
ROOT_FOLDER="1mFMRO1toZdGvD4xObW68QDG8jMTjLxDh"
COLLECTIONS={
 "the-boyz":{"name":"THE BOYZ","folderId":ROOT_FOLDER,"years":{"2019":"1zXctNLe1IJzfPmG5DUIlpZiKNV9YLstH","2020":"1BOATjhs7N6HKaelw0PbbEJOEaagQN3CP","2021":"1nbZPmPjRYny3acbFXzXH7vkVPegQSj1a","2022":"1bdRUhpz9p1KwrUAXQWGbVnPLs4G4l05n","2023":"1mNfxHZEM20onfvifFaUtlp0BygvUPYy9","2024":"1Auu9bxybSC1NHq67zJ1rw9NNCeCAYAuS","2025":"1gzvoJybNKvnICI4SDOvq8VOsumF0zhCR","2026":"18AgkGN3CKR4zAYfYy6L7EhrENZs2CFTj"}},
 "jacob":{"name":"JACOB","folderId":"1LcAtnl8eFdhJPvWC88fkufSKonvuH3Hg"},
 "kevin":{"name":"KEVIN","folderId":"1tdScccylqH1tSeO4kgZbSzHntTcGVBLZ"},
 "eric":{"name":"ERIC","folderId":"1G9bJgSMM7DNt3BA72U-kykSWCP03n_nz"},
}
FIELDS="nextPageToken,files(id,name,mimeType,size,modifiedTime,videoMediaMetadata(width,height,durationMillis))"

def list_folder(folder_id):
 files=[];page_token=None
 while True:
  params={"q":f"'{folder_id}' in parents and trashed=false","key":API_KEY,"pageSize":1000,"orderBy":"name","fields":FIELDS}
  if page_token:params["pageToken"]=page_token
  url="https://www.googleapis.com/drive/v3/files?"+urllib.parse.urlencode(params)
  for attempt in range(5):
   try:
    request=urllib.request.Request(url,headers={"User-Agent":"tbzarchive-github-sync/1.0"})
    with urllib.request.urlopen(request,timeout=45) as response:page=json.load(response)
    break
   except Exception:
    if attempt==4:raise
    time.sleep(1.5*(attempt+1))
  files.extend(page.get("files",[]));page_token=page.get("nextPageToken")
  if not page_token:return files

def clean_video(item,collection,year):
 original_name=item["name"].strip();title=re.sub(r"\.(mp4|mov|m4v|webm)$","",original_name,flags=re.I);title=re.sub(r"^\d+\.\s*","",title).strip();date=""
 match=re.match(r"^(\d{6}|\d{8})\b\s*",title)
 if match:
  code=match.group(1)
  parsed_year,month,day=(2000+int(code[:2]),int(code[2:4]),int(code[4:6])) if len(code)==6 else (int(code[:4]),int(code[4:6]),int(code[6:8]))
  if 2017<=parsed_year<=2035 and 1<=month<=12 and 1<=day<=31:
   date=f"{parsed_year:04d}-{month:02d}-{day:02d}";year=str(parsed_year);title=title[match.end():].strip() or title
 tiktok_id="".join(re.findall(r"\[(\d{15,22})\]",original_name));metadata=item.get("videoMediaMetadata") or {}
 return {"id":item["id"],"title":title,"originalName":original_name,"collection":collection,"year":int(year) if str(year).isdigit() else 0,"date":date,"tiktokId":tiktok_id,"duration":int(metadata.get("durationMillis") or 0),"width":int(metadata.get("width") or 0),"height":int(metadata.get("height") or 0)}

def gather_tree(collection_key,folder_id,fallback_year=""):
 queue=[(folder_id,fallback_year)];videos=[]
 while queue:
  batch,queue=queue[:12],queue[12:]
  with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:results=list(executor.map(lambda row:(row,list_folder(row[0])),batch))
  for (_,path_year),items in results:
   for item in items:
    if item["mimeType"]==FOLDER_MIME:
     child_year=item["name"] if item["name"].isdigit() else path_year;queue.append((item["id"],child_year))
    elif item["mimeType"].startswith("video/"):
     videos.append(clean_video(item,collection_key,path_year or item.get("modifiedTime","")[:4]))
 return videos

def main():
 if not API_KEY:raise SystemExit("Missing GOOGLE_DRIVE_API_KEY. Add it as a GitHub Actions repository secret.")
 discovered=dict(COLLECTIONS["the-boyz"]["years"])
 for item in list_folder(ROOT_FOLDER):
  if item["mimeType"]==FOLDER_MIME and re.fullmatch(r"20\d{2}",item["name"]):discovered[item["name"]]=item["id"]
 jobs=list(discovered.items())
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:official=list(executor.map(lambda row:gather_tree("the-boyz",row[1],row[0]),jobs))
 all_data={"the-boyz":[video for group in official for video in group]}
 for key in ("jacob","kevin","eric"):all_data[key]=gather_tree(key,COLLECTIONS[key]["folderId"])
 for videos in all_data.values():videos.sort(key=lambda video:(video["year"],video["date"],len(video["tiktokId"]),video["tiktokId"],video["title"]),reverse=True)
 output={"sourceFolder":ROOT_FOLDER,"collections":{}}
 for key,info in COLLECTIONS.items():output["collections"][key]={"name":info["name"],"folderId":info["folderId"],"videos":all_data[key]}
 payload=json.dumps(output,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
 (Path(__file__).resolve().parents[1]/"data.js").write_text("window.TIKTOK_ARCHIVE_DATA="+payload+";\n",encoding="utf-8")
 for key,videos in all_data.items():print(f"{key}: {len(videos)} videos")
 print(f"total: {sum(len(videos) for videos in all_data.values())} videos")
if __name__=="__main__":main()


