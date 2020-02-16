from flask import render_template, request, Flask
import PyPDF2 
import logging
import os
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from pathlib import Path
import uuid
from pyzbar.pyzbar import decode
from PIL import Image
import jwt
import json
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

@app.route('/',methods=['POST','GET'])
def upload_pdf():
      if request.method == 'GET':
         return render_template('page.html')
      if request.method == 'POST':
                print(app.instance_path)
                fname=str(uuid.uuid1())
                os.makedirs(os.path.join(app.instance_path, 'tmpfiles',fname), exist_ok=True)
                f=request.files['pdffile']
                f.save(os.path.join(app.instance_path, 'tmpfiles', fname,secure_filename(f.filename)))
                try:
                  PyPDF2.PdfFileReader(open(os.path.join(app.instance_path, 'tmpfiles', fname,secure_filename(f.filename)), "rb"))
                  pages = convert_from_path(os.path.join(app.instance_path, 'tmpfiles', fname,secure_filename(f.filename)),800)
                  i=0
                  foundqrcode=False
                  for page in pages:
                    i=i+1
                    page.save(os.path.join(app.instance_path, 'tmpfiles', fname,Path(secure_filename(f.filename)).stem+"-"+str(i)+".jpg"), 'JPEG')
                    signed_qrcode = decode(Image.open(os.path.join(app.instance_path, 'tmpfiles', fname,Path(secure_filename(f.filename)).stem+"-"+str(i)+".jpg")))
                    if(len(signed_qrcode)>0):
                      foundqrcode=True
                      return processqrcode(signed_qrcode)
                except PyPDF2.utils.PdfReadError:
                  os.remove(os.path.join(app.instance_path, 'tmpfiles', fname,secure_filename(f.filename)))
                  return "invalid PDF file"
                os.remove(os.path.join(app.instance_path, 'tmpfiles', fname,secure_filename(f.filename)))
                return 'Success'

def processqrcode(signed_qrcode):
    public_key=open("einv_sandbox.pem", "r").read()
    ret={}
    for qrcode in signed_qrcode:
       ret['qrcode_signed']=qrcode.data 
       try:
          ret['qrcode_validated']=jwt.decode(qrcode.data,public_key,algorithms='RS256') 
       except:
          ret['qrcode_validated']={}
    return render_template('page.html',signed_qrcode=ret['qrcode_signed'],val_qrcode=json.dumps(ret['qrcode_validated']))

if __name__ == "__main__":
    app.run()
